# bird-recognition

## Preview

![](https://i.imgur.com/RwzYybX.jpeg)

![](https://i.imgur.com/mg2XO7A.jpeg)

## 项目安装

### Python依赖项安装

`pip install -r requirements.txt`

### 配置环境变量

1. 在项目根路径下创建`.env`文件

```text
# 设置YOLO模型的权重路径(默认使用yolov8n)
WEIGHTS_PATH=path/to/your/weights

# 设置置信度阈值(默认0.25)
YOLO_CONF_THRESHOLD=0.5

# 设置deepseek的api
DEEPSEEK_API_KEY=your_api_key
```

### 运行项目

`python main.py`

### API 文档

运行项目后见<http://localhost:8000/docs>

## 项目结构

```text
.
├── README.md                     # 项目说明文档
├── detectors/                   # 模型调用模块（如 YOLOv8）
│   ├── __init__.py              # 包初始化
│   └── yolov8.py                # YOLOv8 检测模型封装
├── main.py                      # 程序主入口，FastAPI 应用启动点
├── requirements.txt             # Python 项目依赖列表
├── routers/                     # 路由模块，定义 API 路由
│   ├── __init__.py              # 包初始化
│   ├── deepseek.py              # 与 DeepSeek 模型相关的接口
│   ├── web.py                   # Web 前端相关的 API 接口
│   ├── wikipeida_api.py         # Wikipedia 查询相关接口（注：文件名可能有误，应为 wikipedia_api.py）
│   └── yolo.py                  # YOLO 模型相关接口
├── schemas/                     # 数据模型定义（Pydantic 模型）
│   ├── __init__.py              # 包初始化
│   └── yolo.py                  # 与 YOLO 检测相关的请求/响应数据结构
└── static/                      # 静态资源文件夹（用于 Web 页面展示）
    ├── about.html               # 关于页面
    ├── images/                  # 图像资源文件夹
    ├── index.html               # 首页 HTML 文件
    ├── script.js                # 前端交互逻辑脚本
    └── style.css                # 页面样式文件

7 directories, 19 files

```
