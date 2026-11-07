import os
import numpy as np
import torch
import torch.nn.functional as F
from matplotlib import pyplot as plt
from sklearn.metrics import jaccard_score, f1_score
from torch import nn
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms.functional as TF
import torchvision.transforms as transforms
import random
from tqdm import tqdm
from PIL import Image
from transformers import Mask2FormerForUniversalSegmentation, AutoImageProcessor
 
torch.backends.cudnn.benchmark = True
 
 
# ==================== Dice Loss（支持上采样 + 忽略指定类）====================
class DiceLoss(nn.Module):
    def __init__(self, ignore_index=0):
        """
        ignore_index: 忽略的类别标签（例如背景0，不参与Dice计算）
        """
        super().__init__()
        self.ignore_index = ignore_index
 
    def forward(self, masks_queries_logits, class_queries_logits, targets):
        """
        masks_queries_logits: [B, Q, H_feat, W_feat]
        class_queries_logits: [B, Q, C]  其中 C = num_labels + 1（自动包含背景+void）
        targets: [B, H_img, W_img]  原始图像尺寸的标签（值范围 0~num_labels-1，其中0为忽略的背景类）
        """
        B, Q, H_feat, W_feat = masks_queries_logits.shape
        C = class_queries_logits.shape[-1]  # 模型实际输出类别数
 
        # 1. 融合得到像素级 logits（下采样特征尺寸）
        masks_probs = torch.softmax(masks_queries_logits, dim=1)  # [B, Q, H_feat, W_feat]
        pixel_logits = torch.einsum("bqhw,bqc->bchw", masks_probs, class_queries_logits)  # [B, C, H_feat, W_feat]
 
        # 2. 上采样到与 targets 相同空间尺寸
        pixel_logits = F.interpolate(pixel_logits, size=targets.shape[-2:], mode='bilinear', align_corners=False)
 
        # 3. 计算 softmax 概率
        preds = torch.softmax(pixel_logits, dim=1)  # [B, C, H, W]
 
        # 4. 将 targets 转为 one-hot
        targets_onehot = torch.nn.functional.one_hot(targets.long(), C).permute(0, 3, 1, 2).float()
 
        # 5. 如果设置了 ignore_index，则将该类在 targets_onehot 中的贡献置为0
        if self.ignore_index is not None and 0 <= self.ignore_index < C:
            targets_onehot[:, self.ignore_index] = 0
 
        smooth = 1e-5
        intersection = (preds * targets_onehot).sum(dim=(2, 3))
        union = preds.sum(dim=(2, 3)) + targets_onehot.sum(dim=(2, 3))
 
        dice = (2. * intersection + smooth) / (union + smooth)
 
        # 计算平均 Dice 时排除 ignore_index
        if self.ignore_index is not None and 0 <= self.ignore_index < C:
            mask = torch.ones(C, device=dice.device)
            mask[self.ignore_index] = 0
            dice = dice * mask
            dice_mean = dice.sum() / mask.sum()
        else:
            dice_mean = dice.mean()
 
        return 1 - dice_mean
 
 
# ==================== 数据增强 ====================
class PairedTransformTrain:
    def __call__(self, image, mask):
        if random.random() > 0.5:
            image = TF.hflip(image)
            mask = TF.hflip(mask)
        if random.random() > 0.5:
            image = TF.vflip(image)
            mask = TF.vflip(mask)
        if random.random() > 0.5:
            angle = random.uniform(-30, 30)
            image = TF.rotate(image, angle)
            mask = TF.rotate(mask, angle)
 
        image = TF.resize(image, (400, 400), Image.BILINEAR)
        mask = TF.resize(mask, (400, 400), Image.NEAREST)
 
        i, j, h, w = transforms.RandomCrop.get_params(image, output_size=(384, 384))
        image = TF.crop(image, i, j, h, w)
        mask = TF.crop(mask, i, j, h, w)
 
        image = transforms.ColorJitter(0.3, 0.3, 0.3)(image)
        return image, mask
 
 
class PairedTransformVal:
    def __call__(self, image, mask):
        image = TF.resize(image, (384, 384), Image.BILINEAR)
        mask = TF.resize(mask, (384, 384), Image.NEAREST)
        return image, mask
 
 
# ==================== 数据集（假设原始标签为1~115，我们将其转换为0~114，0作为忽略背景类）====================
class PlantSegV2Dataset(Dataset):
    def __init__(self, images_dir, masks_dir, processor, transform=None):
        self.processor = processor
        self.transform = transform
        self.images, self.masks = [], []
 
        for root, _, files in os.walk(images_dir):
            for file in files:
                if file.endswith(('.jpg', '.png', '.jpeg')):
                    img_path = os.path.join(root, file)
                    mask_path = os.path.join(masks_dir, os.path.relpath(img_path, images_dir))
                    mask_path = os.path.splitext(mask_path)[0] + ".png"
                    if os.path.exists(mask_path):
                        self.images.append(img_path)
                        self.masks.append(mask_path)
 
    def __len__(self):
        return len(self.images)
 
    def __getitem__(self, idx):
        image = Image.open(self.images[idx]).convert("RGB")
        mask = Image.open(self.masks[idx]).convert("L")
 
        if self.transform:
            image, mask = self.transform(image, mask)
 
        # 原始mask值假设为1~115，我们转换为0~114（0用于忽略背景或不存在）
        # 如果mask中包含0（未标注区域），也将其视为忽略类（0）
        mask_np = np.array(mask, dtype=np.int64)
        # 将1~115映射为0~114，其他值（如0或>115）设为0（忽略）
        mask_np = np.where((mask_np >= 1) & (mask_np <= 115), mask_np - 1, 0)
 
        # 确保值在0~114范围内
        mask_np = np.clip(mask_np, 0, 114)
 
        inputs = self.processor(images=image, segmentation_maps=mask_np, return_tensors="pt")
 
        return (
            inputs["pixel_values"].squeeze(0),
            inputs["mask_labels"][0],
            inputs["class_labels"][0],
            torch.from_numpy(mask_np)
        )
 
 
def collate_fn(batch):
    return (
        torch.stack([b[0] for b in batch]),
        [b[1] for b in batch],
        [b[2] for b in batch],
        torch.stack([b[3] for b in batch])
    )
 
 
# ==================== 主函数 ====================
def main():
    model_path = "/root/autodl-tmp/mask2former_local"
 
    train_img_dir = "./data/plantsegv2/images/train"
    train_mask_dir = "./data/plantsegv2/annotations/train"
 
    val_img_dir = "./data/plantsegv2/images/test"
    val_mask_dir = "./data/plantsegv2/annotations/test"
 
    # 有效前景类别数为115（原始1~115）
    num_foreground_classes = 115
    processor = AutoImageProcessor.from_pretrained(model_path)
    model = Mask2FormerForUniversalSegmentation.from_pretrained(
        model_path,
        num_labels=num_foreground_classes,
        ignore_mismatched_sizes=True
    )
 
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
 
    train_loader = DataLoader(
        PlantSegV2Dataset(train_img_dir, train_mask_dir, processor, PairedTransformTrain()),
        batch_size=4, shuffle=True, num_workers=4, collate_fn=collate_fn
    )
 
    val_loader = DataLoader(
        PlantSegV2Dataset(val_img_dir, val_mask_dir, processor, PairedTransformVal()),
        batch_size=4, shuffle=False, num_workers=4, collate_fn=collate_fn
    )
 
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-5)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=30)
 
    # DiceLoss 忽略背景类（索引0）
    dice_loss = DiceLoss(ignore_index=0)
 
    best_miou = 0
    patience, counter = 5, 0
 
    # 评估的类别：有效类别索引1~115（对应原始标签2~116? 注意模型输出0为背景，1~115对应我们的0~114? 实际上我们的标签0~114映射到模型输出的1~115。因此在评估时需要将预测值减1或者调整。
    # 后处理 post_process_semantic_segmentation 返回的值范围是0~num_labels，即0~115。其中0是背景（void），1~115对应我们数据集的0~114。
    # 我们需要将预测值和真值都映射回原始标签空间1~115进行评估。最简单：只考虑真值>0的像素，预测值>0且对应类别减1？或者直接使用模型输出的预测值（1~115）和原始标签（1~115）比较。
    # 由于我们在数据集中将原始标签减1变成了0~114，因此评估时应该加1。下面采用加1的方法。
    # 但注意预测值中可能包含0（背景），背景像素我们忽略不计。
 
    # 定义评估时使用的标签列表（原始1~115）
    eval_labels = list(range(1, 116))  # 115类
 
    for epoch in range(30):
        model.train()
        total_loss = 0
 
        for pixel_values, mask_labels, class_labels, original_masks in tqdm(train_loader):
            pixel_values = pixel_values.to(device)
            mask_labels = [m.to(device) for m in mask_labels]
            class_labels = [c.to(device) for c in class_labels]
            original_masks = original_masks.to(device)  # 实际标签0~114
 
            optimizer.zero_grad()
            outputs = model(pixel_values=pixel_values, mask_labels=mask_labels, class_labels=class_labels)
 
            ce_loss = outputs.loss
 
            masks_queries_logits = outputs.masks_queries_logits
            class_queries_logits = outputs.class_queries_logits
            dice = dice_loss(masks_queries_logits, class_queries_logits, original_masks)
 
            loss = ce_loss + 0.5 * dice
 
            loss.backward()
            optimizer.step()
 
            total_loss += loss.item()
 
        scheduler.step()
 
        # ==================== 验证 ====================
        model.eval()
        all_preds_orig = []  # 存储原始标签空间（1~115）的预测值
        all_masks_orig = []  # 存储原始标签空间（1~115）的真实值
 
        with torch.no_grad():
            for pixel_values, _, _, original_masks in val_loader:
                pixel_values = pixel_values.to(device)
                outputs = model(pixel_values=pixel_values)
 
                target_sizes = [m.shape for m in original_masks]
                # preds 是 list of torch.Tensor，每个shape [H,W]，值范围0~115
                preds = processor.post_process_semantic_segmentation(outputs, target_sizes=target_sizes)
 
                for p, m in zip(preds, original_masks):
                    p_np = p.cpu().numpy()  # 模型预测，0~115
                    m_np = m.cpu().numpy()  # 真实标签0~114
                    # 将真实标签加1变回原始1~115（0变为1？不对，真实标签0是忽略背景，在原始中背景不存在，所以真实标签0不应参与评估）
                    # 我们只评估 m_np > 0 的区域（即原始有标注的区域）
                    valid_mask = m_np > 0
                    if valid_mask.sum() > 0:
                        # 真实标签加1恢复原始值
                        m_orig = m_np[valid_mask] + 1
                        # 预测值中对应区域的值：如果预测值为0则视为背景（忽略），但背景不属于类别，需要排除吗？我们只考虑预测值在1~115范围内
                        p_orig = p_np[valid_mask]
                        # 进一步过滤：预测值也在1~115之间
                        valid_pred = (p_orig >= 1) & (p_orig <= 115)
                        # 如果不满足，可将其赋值为某个无效值，但需要一致长度。简单做法：只保留同时满足真值有效且预测值有效
                        # 更稳健：对于预测值0或>115的区域，我们不参与计算，但那样会减少样本。直接保留预测值，但jaccard_score要求标签在labels范围内，超出会报错。我们将预测值clip到1~115。
                        p_orig = np.clip(p_orig, 1, 115)
                        all_preds_orig.append(p_orig)
                        all_masks_orig.append(m_orig)
 
        if len(all_preds_orig) > 0:
            all_preds_orig = np.concatenate(all_preds_orig)
            all_masks_orig = np.concatenate(all_masks_orig)
            miou = jaccard_score(all_masks_orig, all_preds_orig, average='macro', labels=eval_labels, zero_division=0)
        else:
            miou = 0.0
            print("Warning: No valid pixels in validation set")
 
        print(f"\nEpoch {epoch + 1} Loss:{total_loss:.3f} mIoU:{miou:.4f}")
 
        if miou > best_miou:
            best_miou = miou
            torch.save(model.state_dict(), "best_segmentation_model.pth")
            counter = 0
        else:
            counter += 1
            if counter >= patience:
                print("Early stop")
                break
 
 
if __name__ == "__main__":
    main()
