# bird-recognition

## Preview

![](https://i.imgur.com/drR5gQ6.jpeg)

![](https://i.imgur.com/nX8i6HI.jpeg)

## 项目安装

### 仓库克隆

```bash
git clone https://github.com/pipi4/bird-recognition
cd bird-recognition
```

### Python环境

激活python虚拟环境后使用下面命令安装依赖项：

```bash
pip install -r requirements.txt
```

### 配置环境变量

1. 在项目根路径下创建`.env`文件

```text
# 设置YOLO模型的权重路径(默认使用yolov8n)
WEIGHTS_PATH=path/to/your/weights

# 设置置信度阈值(默认0.25)
YOLO_CONF_THRESHOLD=0.5
```

### Ollama大模型

安装[Ollama](https://ollama.com)后，运行下面命令拉取使用鸟类数据微调后的deepseek-r1:1.5b大语言模型：

```bash
ollama pull hf.co/pipa223/deepseekr1_1.5b_bird2
```

运行大模型

```bash
ollama serve
```

### 运行项目

`python main.py`

### API 文档

运行项目后见<http://localhost:8000/docs>

## 项目结构

```text
.
├── best.pt                 # 最优模型文件
├── database.py             # 数据库交互文件
├── detectors               # 检测器目录
│   ├── __init__.py         # 初始化文件
│   └── yolov8.py           # YOLOv8检测器实现
├── docs                    # 文档目录
│   ├── about.md            # 关于页面文档
│   └── index.md            # 首页文档
├── main.py                 # 主程序文件
├── mkdocs.yml              # MkDocs配置文件
├── README.md               # 项目README文件
├── requirements.txt        # 依赖项列表
├── routers                 # 路由器目录
│   ├── __init__.py         # 初始化文件
│   ├── llm.py              # 语言模型路由器
│   ├── speech.py           # 语音路由器
│   ├── web.py              # 网页路由器
│   ├── wikipeida_api.py    # 维基百科API路由器
│   └── yolo.py             # YOLO路由器
├── schemas                 # 模式目录
│   ├── __init__.py         # 初始化文件
│   └── yolo.py             # YOLO模式定义
└── static                  # 静态文件目录
    ├── about.html          # 关于页面
    ├── camera.js           # 相机处理脚本
    ├── chat.js             # 聊天脚本
    ├── images              # 图像目录
    ├── index.html          # 首页
    ├── landing.css         # 登陆页面样式
    ├── landing.html        # 登陆页面
    ├── processor.worker.js # 处理器工作线程
    ├── script.js           # 主脚本文件
    ├── style.css           # 样式文件
    └── tts.js              # 文本到语音脚本

7 directories, 28 files

```
