#  BirdFinder 智能鸟类识别系统
基于 YOLOv8 与本地大语言模型的图像识别 + AI 问答系统，集成前端交互、语音助手、异常预警与数据看板功能，适用于生态监测、科普教育等多场景应用。

## 目录
- [Preview](#preview)
- [项目特色](#项目特色)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [项目安装](#项目安装)
  - [仓库克隆](#仓库克隆)
  - [Python环境](#python环境)
  - [配置环境变量](#配置环境变量)
  - [Ollama大模型](#ollama大模型)
  - [运行项目](#运行项目)
  - [API 文档](#api-文档)
- [模型训练](#模型训练)
  - [YOLO鸟类识别模型](#YOLO鸟类识别模型)
  - [Deepseek鸟类专家模型微调](#Deepseek鸟类专家模型微调)
- [使用说明](#使用说明)
- [注意事项](#注意事项)
- [开发团队](#开发团队)

## Preview

![](https://i.imgur.com/drR5gQ6.jpeg)

![](https://i.imgur.com/nX8i6HI.jpeg)

## 项目特色
鸟类图像识别：基于 YOLOv8 模型，支持 200 种鸟类识别，准确高效。

百科集成：自动获取 Wikipedia 鸟类资料并展示。

AI 问答助手：集成本地部署的 DeepSeek-R1 模型，通过 Ollama 调用微调模型 API 进行智能问答。

语音助手：支持语音输入和播报（基于讯飞语音 WebAPI），实现自然语言语音交互。

异常预警机制：用户可自定义监测物种，系统检测后自动触发弹窗与语音提醒。

数据看板：展示检测数量、预警趋势、问答记录等核心统计数据。

历史记录管理：查看历史识别时间、目标物种和识别图像。

暗夜模式：贴心夜间界面切换，舒适护眼。

## 技术栈

| 模块    | 技术                                    |
| ----- | ------------------------------------- |
| 前端    | HTML + CSS + JavaScript（支持暗夜模式、语音交互）  |
| 后端    | Python + FastAPI<br>                  |
| 模型    | YOLOv8（目标检测） + DeepSeek-R1 本地微调（语言模型） |
| 数据集   | CUB-200-2011 鸟类识别数据集<br>              |
| 语音处理  | 科大讯飞语音识别 + 合成 WebAPI                  |
| 第三方集成 | Wikipedia API、Ollama                  |

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
    ├── images              # 图像目录
    ├── index.html          # 首页
    ├── landing.css         # 登陆页面样式
    ├── landing.html        # 登陆页面
    ├── script.js           # 主脚本文件
    └── style.css           # 样式文件
    

7 directories, 28 files

```

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


## 模型训练

### YOLO鸟类识别模型

Step1: 下载[CUB-200-2011](https://data.caltech.edu/records/65de6-vp158)数据集：

```bash
wget -O CUB_200_2011.tgz "https://data.caltech.edu/records/65de6-vp158/files/CUB_200_2011.tgz?download=1"
```

Step2: 将数据转换为YOLO格式

[相关代码](https://gist.github.com/oodenough/445cff39ab5f2a9dd259ee0185ae8b8b)

Step3: 超参数调整

参考[Ultralytics YOLO Hyperparameter Tuning Guide - Ultralytics YOLO Docs](https://docs.ultralytics.com/guides/hyperparameter-tuning/)

我们的[超参数调整代码](https://gist.github.com/oodenough/aef6579ec52a765e6cc9c6dcdf831f5f)

Step4: 模型训练

我们的[训练代码](https://gist.github.com/oodenough/44b3456156dcb1c20bd3a938e18de88b)

### Deepseek鸟类专家模型微调

我们的[colab 微调代码](https://colab.research.google.com/drive/1IWphlU8njqhAbYdlG_6H8iQrAI7e7hcV?usp=share_link#scrollTo=POnl9EzqVs3G)

## 使用说明
上传鸟类图片进行识别

系统展示识别结果与百科信息

可输入或语音提问鸟类相关问题

配置预警物种后，识别到将触发实时预警

浏览数据看板，查看统计趋势与问答记录


## 注意事项
项目为教学与实验性质使用，如需线上部署请注意 API 安全性配置

语音接口需申请讯飞开发者账号并配置相应参数

## 开发团队
项目成员：皮文浩、肖艳平、官家浩

指导老师：钟佳杭
