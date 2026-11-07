from huggingface_hub import snapshot_download
import os
 
# 下载到指定文件夹（如 ./mask2former_local）
local_dir = "./mask2former_local"
os.makedirs(local_dir, exist_ok=True)
 
snapshot_download(
    repo_id="facebook/mask2former-swin-small-ade-semantic",
    local_dir=local_dir,
    local_dir_use_symlinks=False,
    ignore_patterns=["*.h5", "*.ot", "msgpack"]  # 可忽略不必要的大文件
)
print(f"✅ 模型已下载到 {local_dir}")


附录：项目架构总览
PlantDoctor/
├── app.py                          # Flask 主入口，路由注册，认证逻辑
├── config.py                       # 全局配置（路径、API Key、阈值等）
├── requirements.txt                # Python 依赖清单
├── preprocessor_config.json        # Mask2Former 图像预处理器配置
│
├── controllers/                    # 控制器层（Blueprint 路由）
│   ├── __init__.py
│   ├── dashboard_routes.py         # 仪表盘（首页统计、养护建议）
│   ├── diagnose_routes.py          # 核心诊断（图片上传、AI预测、LLM治疗）
│   └── knowledge_routes.py         # 知识库（病害百科、病历档案）
│
├── models/                         # 模型层（数据访问 + 业务逻辑）
│   ├── __init__.py
│   ├── database.py                 # SQLite 数据库 CRUD 操作
│   ├── knowledge_base.py           # 38 种植物病害专家知识库
│   └── model_loader.py             # 深度学习模型加载与异步推理
│
├── utils/                          # 工具层
│   ├── __init__.py
│   ├── image_utils.py              # 图像处理（掩码融合、严重度计算）
│   └── logging_utils.py            # 日志与异常处理装饰器
│
├── static/css/
│   └── style.css                   # 全局样式（玻璃拟态 + 响应式）
│
├── templates/                      # Jinja2 前端模板
│   ├── base.html                   # 基础布局（导航栏 + 页脚）
│   ├── login.html                  # 登录页面
│   ├── register.html               # 注册页面
│   ├── dashboard.html              # 仪表盘（统计卡片 + 养护建议）
│   ├── diagnose.html               # 智能诊断（拖拽上传 + 双栏预览）
│   └── knowledge.html              # 知识百科（分类筛选 + 病历管理）
│
├── classification.py               # EfficientNet-V2 分类模型训练脚本
├── segment.py                      # Mask2Former 分割模型训练脚本
└── test.py                         # HuggingFace 模型下载脚本

核心技术指标
