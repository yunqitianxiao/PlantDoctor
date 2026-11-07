from typing import Optional
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from torchvision.models import efficientnet_v2_s
from PIL import Image
import os
import numpy as np
from sklearn.metrics import roc_curve, auc, roc_auc_score, classification_report, f1_score, recall_score, \
    precision_score
import matplotlib.pyplot as plt
from tqdm import tqdm
from sklearn.model_selection import train_test_split
 
torch.backends.cudnn.benchmark = True
 
path = './data/PlantVillage'
 
data_enhance_train = transforms.Compose([
    transforms.RandomHorizontalFlip(),
    transforms.RandomVerticalFlip(),
    transforms.RandomRotation(15),
    transforms.RandomResizedCrop(384, scale=(0.8, 1.0)),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])
 
data_enhance_val = transforms.Compose([
    transforms.Resize(400),
    transforms.CenterCrop(384),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])
 
data_enhance_test = transforms.Compose([
    transforms.Resize(400),
    transforms.CenterCrop(384),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])
 
 
class PlantVillageDataset(Dataset):
    def __init__(self, root_dir, transform=None, split='train'):
        self.root_dir = root_dir
        self.transform = transform
        self.split = split
        folder = 'train' if split == 'train' else 'val'
        self.data_dir = os.path.join(root_dir, folder)
 
        self.classes = sorted([d for d in os.listdir(self.data_dir) if os.path.isdir(os.path.join(self.data_dir, d))])
        self.class_to_idx = {cls_name: idx for idx, cls_name in enumerate(self.classes)}
 
        self.image_paths = []
        self.labels = []
 
        for class_name in self.classes:
            class_dir = os.path.join(self.data_dir, class_name)
            class_idx = self.class_to_idx[class_name]
            for img_name in os.listdir(class_dir):
                if img_name.lower().endswith(('.jpg', '.jpeg', '.png')):
                    self.image_paths.append(os.path.join(class_dir, img_name))
                    self.labels.append(class_idx)
 
        if split != 'train':
            paths_train, paths_test, labels_train, labels_test = train_test_split(
                self.image_paths, self.labels, test_size=0.5, stratify=self.labels, random_state=42
            )
            if split == 'val':
                self.image_paths, self.labels = paths_train, labels_train
            else:
                self.image_paths, self.labels = paths_test, labels_test
 
    def __len__(self):
        return len(self.image_paths)
 
    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        label = self.labels[idx]
        image = Image.open(img_path).convert('RGB')
        if self.transform:
            image = self.transform(image)
        return image, label
 
 
def train(model, train_loader, val_loader, criterion, optimizer, scheduler, device, epochs, patience):
    best_acc = 0.0
    best_epoch = 0
    counter = 0
 
    # 用于记录训练历史
    train_losses = []
    val_accs = []
 
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        loop = tqdm(train_loader, desc=f'Epoch {epoch + 1}/{epochs}', leave=False)
        for images, labels in loop:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            loop.set_postfix(loss=loss.item())
 
        avg_loss = train_loss / len(train_loader)
        train_losses.append(avg_loss)
 
        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                _, predicted = torch.max(outputs, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
        acc = 100 * correct / total
        val_accs.append(acc)
 
        print(f"Epoch [{epoch + 1}/{epochs}] Loss: {avg_loss:.4f} Acc: {acc:.2f}%")
        scheduler.step()
 
        # 早停机制
        if acc > best_acc:
            best_acc = acc
            best_epoch = epoch + 1
            torch.save(model.state_dict(), 'best_classification_model.pth')
            counter = 0  # 重置计数器
            print(f"  ✓ 新的最佳模型！准确率: {best_acc:.2f}%")
        else:
            counter += 1
            print(f"  ✗ 验证准确率未提升。早停计数: {counter}/{patience}")
 
        # 早停判断
        if counter >= patience:
            print(f"\n{'=' * 50}")
            print(f"早停触发！")
            print(f"最佳 epoch: {best_epoch}")
            print(f"最佳验证准确率: {best_acc:.2f}%")
            print(f"{'=' * 50}")
            break
 
    # 绘制训练曲线（可选）
    plt.figure(figsize=(12, 4))
    plt.subplot(1, 2, 1)
    plt.plot(train_losses, label='Training Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title('Training Loss Curve')
    plt.legend()
    plt.grid(True)
 
    plt.subplot(1, 2, 2)
    plt.plot(val_accs, label='Validation Accuracy', color='orange')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy (%)')
    plt.title('Validation Accuracy Curve')
    plt.legend()
    plt.grid(True)
 
    plt.tight_layout()
    plt.savefig('training_curves.png', dpi=300, bbox_inches='tight')
    plt.show()
 
    return best_acc
 
 
def test(model, test_loader, device, class_names):
    model.load_state_dict(torch.load('best_classification_model.pth'))
    model.eval()
 
    correct = 0
    total = 0
    with torch.no_grad():
        for images, labels in test_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
    test_acc = 100 * correct / total
    print(f"\n测试集准确率: {test_acc:.2f}%")
 
    all_probs = []
    all_labels = []
    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            outputs = model(images)
            probs = torch.softmax(outputs, dim=1).cpu().numpy()
            all_probs.append(probs)
            all_labels.append(labels.numpy())
 
    all_probs = np.vstack(all_probs)
    all_labels = np.hstack(all_labels)
 
    macro_auc = roc_auc_score(all_labels, all_probs, multi_class='ovr', average='macro')
    print(f"Macro AUC: {macro_auc:.4f}")
 
    plt.figure(figsize=(10, 8))
    for i in range(len(class_names)):
        fpr, tpr, _ = roc_curve(all_labels == i, all_probs[:, i])
        roc_auc = auc(fpr, tpr)
        plt.plot(fpr, tpr, lw=1, label=f'{class_names[i]} (AUC={roc_auc:.3f})')
    plt.plot([0, 1], [0, 1], 'k--', lw=2)
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Multi-class ROC Curve (One-vs-Rest)')
    plt.legend(loc="lower right", fontsize='small')
    plt.savefig('classification_roc_curve.png', dpi=300, bbox_inches='tight')
    plt.show()
 
    all_preds = np.argmax(all_probs, axis=1)
    print("=== 分类报告 ===")
    print(classification_report(all_labels, all_preds, target_names=class_names, digits=4))
    print(f"Macro F1: {f1_score(all_labels, all_preds, average='macro'):.4f}")
    print(f"Macro Recall: {recall_score(all_labels, all_preds, average='macro'):.4f}")
    print(f"Macro Precision: {precision_score(all_labels, all_preds, average='macro'):.4f}")
 
 
if __name__ == '__main__':
    train_dataset = PlantVillageDataset(root_dir=path, transform=data_enhance_train, split='train')
    val_dataset = PlantVillageDataset(root_dir=path, transform=data_enhance_val, split='val')
    test_dataset = PlantVillageDataset(root_dir=path, transform=data_enhance_test, split='test')
 
    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True, num_workers=8, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False, num_workers=8, pin_memory=True)
    test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False, num_workers=8, pin_memory=True)
 
    model = efficientnet_v2_s(weights='DEFAULT')
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, 38)
 
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
 
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-2)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=50)
    criterion = nn.CrossEntropyLoss()
 
    best_acc = train(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        criterion=criterion,
        optimizer=optimizer,
        scheduler=scheduler,
        device=device,
        epochs=50,
        patience=8
    )
 
    test(model, test_loader, device, class_names=val_dataset.classes)
