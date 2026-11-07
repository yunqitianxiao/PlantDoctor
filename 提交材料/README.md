# 植物医生 · 植物病害智能诊断系统

基于 **Flask + PyTorch** 的网页版作物病害诊断系统：上传叶片图片，自动识别病害（38 类）、估算病灶严重程度（分割）、生成分级治疗方案，并支持诊断档案、批量检测、知识百科与"我的植物"管理。

## 运行

```bash
pip install -r requirements.txt
python app.py            # 打开 http://localhost:5000
```

首次运行自动建库（`instance/plant_doctor.db`），注册账号后即可诊断。

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Flask（蓝图）、SQLite、Werkzeug 安全、`threading+queue` 异步推理 |
| 分类 | EfficientNet-V2-s（38 类 PlantVillage） |
| 分割 | Mask2Former（Swin 主干，115 类语义分割） |
| 方案生成 | DeepSeek（langchain-openai `ChatOpenAI`） |
| 前端 | 原生 HTML5/CSS/JS、Chart.js、FontAwesome、暗色主题、Canvas 掩码叠加 |

## 主要目录

```
植物医生/
├── app.py                    # 入口，注册蓝图与登录/注册路由
├── config.py                 # 配置（模型路径、DeepSeek、严重度阈值）
├── controllers/              # 页面/接口蓝图（dashboard/diagnose/knowledge/frontend）
├── models/                   # model_loader(推理) / database(库) / knowledge_base(知识)
├── utils/                    # image_utils(图像) / logging_utils(日志+异常装饰)
├── templates/                # 11 个页面模板
├── static/                   # style.css + widgets.css 设计系统 + 9 个 JS 模块
├── classification.py         # 分类训练/推理脚本
├── segment.py                # 分割训练/推理脚本
└── 提交材料/                  # 本交付说明 + 分页源码文档
```

## 关键设计

- **异步推理**：`/api/predict` 把任务放入队列，后台线程调用模型，接口轮询结果，避免阻塞请求。
- **演示模式兜底**：未放置模型权重时自动返回样例结果，页面、建档、导出可完整走通（便于无 GPU 环境验证）。
- **可调病灶叠加**：后端额外回传透明底病灶掩码，前端可在 Canvas 上实时调节透明度与颜色。
- **命令面板**：按 `Ctrl/Cmd + K` 呼出全局命令面板，支持页面跳转、切换主题、打印/导出等操作。

## 需要模型权重才可真实诊断

把以下文件放到项目根目录，并在 `config.py` 中核对路径：

- `best_classification_model.pth`
- `best_segmentation_model.pth`
- `mask2former_local/`（Mask2Former 本地配置）

## 说明

- `config.py` 内含一份 DeepSeek API Key（部署时建议改为环境变量读取）。
- 验证会产生示例数据库与上传图片（`instance/`、`uploads/`）。
