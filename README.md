# 植物医生 · 植物病害智能诊断系统

一个基于 **Flask + PyTorch + DeepSeek** 的植物病害诊断 Web 应用。上传叶片图片后，系统完成病害分类、病斑分割、严重度评估和分级防治建议生成，并保存诊断记录。

## 功能

- **38 类病害分类**：EfficientNet-V2-s 迁移学习，PlantVillage 数据集验证准确率 **96.7%**。
- **115 类病斑分割**：Mask2Former + Swin 主干，项目实测 IoU **≥ 0.75**。
- **四档严重度评估**：按病斑像素占比划分健康 / 轻度 / 中度 / 重度。
- **大模型分级建议**：DeepSeek 结合病害知识与严重度生成治疗方案；未配置 Key 或调用失败时自动回退到本地知识库。
- **完整 Web 流程**：登录注册、单图诊断、批量检测、诊断档案、数据看板、病害百科和“我的植物”。
- **异步推理**：`threading + queue` 将模型推理移出请求线程，避免阻塞 Flask 请求。
- **可视化病斑叠加**：后端返回病灶掩码，前端 Canvas 支持透明度与颜色调节。
- **演示模式**：未放置模型权重时仍可跑通页面、建档和导出流程。

## 技术架构

```text
浏览器上传图片
    │
    ▼
Flask Blueprint ──► 异步推理队列 ──► ModelManager（单例）
                                      ├── EfficientNet-V2-s：38 类分类
                                      └── Mask2Former：115 类病斑分割
    │
    ├── 病斑面积占比 ──► 四档严重度
    ├── DeepSeek ──► 分级防治建议（失败时知识库兜底）
    └── SQLite ──► 诊断历史 / 看板 / 植物档案
```

| 层 | 技术 |
|---|---|
| 后端 | Python、Flask、Flask-Login、SQLite、Werkzeug |
| 视觉模型 | PyTorch、torchvision、EfficientNet-V2-s、HuggingFace Transformers、Mask2Former |
| 大模型 | DeepSeek API、LangChain OpenAI Compatible |
| 前端 | HTML5、CSS3、原生 JavaScript、Chart.js、Canvas |

## 快速开始

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# 在 .env 中填写 DEEPSEEK_API_KEY；不填也可使用知识库兜底
python app.py
```

打开 <http://localhost:5000>，注册账号后即可使用。

## 模型权重

仓库不包含大体积数据集和权重。真实推理需要将以下文件放到项目根目录，并在 `config.py` 中核对路径：

- `best_classification_model.pth`
- `best_segmentation_model.pth`
- `mask2former_local/`（Mask2Former 本地配置与权重）

缺少权重时会进入演示模式，不影响前端流程和数据库功能验证。

## 目录结构

```text
.
├── app.py                     # Flask 入口与登录/注册
├── config.py                  # 路径、模型与 API 配置
├── controllers/               # 页面 / 诊断 / 看板 / 知识库路由
├── models/                    # 模型加载、数据库、病害知识库
├── utils/                     # 图像处理与日志
├── templates/                 # Jinja2 页面模板
├── static/                    # CSS / JavaScript / 图片
├── classification.py          # 分类训练与推理脚本
├── segment.py                 # 分割训练与推理脚本
├── test.py                    # 项目自检脚本
└── requirements.txt
```

## 数据与隐私

- 数据集、模型权重、运行数据库、上传图片和 `.env` 均不纳入版本控制。
- 部署前请设置随机 `SECRET_KEY`，并通过环境变量提供 `DEEPSEEK_API_KEY`。

## 说明

分类准确率与分割 IoU 来自项目训练/验证记录；实际田间效果会受光照、拍摄角度、背景和病害阶段影响，诊断结果仅作辅助参考。
