# 基于YOLOv8和DeepSeek API的智能图像识别与问答系统

## 一、项目背景与目标

本项目旨在构建一个基于图像识别与大语言模型能力的多模态问答系统，支持用户上传图像进行物体识别（如鸟类），并在此基础上向 AI 提问，获得智能、语义化的答复。项目集成了 YOLO模型训练目标检测算法与 DeepSeek 大语言模型，通过 FastAPI 构建服务端接口，具备一定的交互性和扩展性。

## 二、技术栈

- **后端框架**：FastAPI  
- **目标检测**：基于YOLO11的鸟类种类识别模型（Ultralytics）  
- **大模型问答**：DeepSeek API  
- **运行环境**：Python 3.9+  
- **依赖管理**：dotenv、torch、opencv-python、ultralytics、openai等

## 三、功能模块划分与思路

本项目由两个核心功能模块构成：

### 1. 图像识别模块（`yolo_v8.py`）

该模块负责处理用户上传的图像，使用 YOLOv8 模型进行目标检测，提取图像中出现的目标（如鸟类物种），并返回检测到的标签集合。主要流程包括：

- 图像字节流转为 OpenCV 图像格式  
- 使用 YOLO 模型进行目标检测  
- 结果图像绘制与标签提取

### 2. 自然语言问答模块（`deepseek.py`）

该模块基于 DeepSeek 提供的 API 实现自然语言处理与回答生成，支持多轮对话及流式响应输出。用户可以基于识别结果向模型提问，由模型返回语义化答案。主要流程包括：

- 用户请求携带问题与 user_id  
- 保存用户对话上下文，实现多轮对话  
- 使用 DeepSeek 的流式接口返回逐步生成的内容

### 2.wiki信息查询模块（wikipeida_api.py）
从 Wikipedia API 获取指定鸟类的概要信息，包括标题、简介、图片链接和维基百科页面的链接。具体流程如下：

1. **定义数据模型**：使用 Pydantic 定义了一个名为 `WikipediaInfo` 的数据模型，表示从 Wikipedia 获取的鸟类信息。该模型包含四个字段：`title`（鸟类名称）、`summary`（简介）、`image`（图片链接，可能为空）、`wiki_url`（维基百科页面链接）。
    
2. **获取 Wikipedia 信息**：定义了一个函数 `get_wikipedia_summary(bird_name)`，它接受一个鸟类名称作为输入。该函数会将名称中的空格替换为下划线，构造 Wikipedia API 的 URL，向该 URL 发送请求，并获取该鸟类的概要信息。
    
3. **处理 API 响应**：
    
    - 如果请求成功（状态码为 200），从返回的 JSON 数据中提取鸟类的标题、简介、图片链接和维基百科页面链接。如果某个字段不存在，则返回默认值（如 "未知"、"暂无介绍"、"无图片"）。
        
    - 如果请求失败，则返回一组默认信息，包括一个指向 Wikipedia 搜索页面的链接，以便用户手动查找。
        
4. **返回结果**：函数最终返回一个字典，包含鸟类的名称、简介、图片链接和维基百科页面的 URL。如果请求失败，返回的结果包含默认的错误信息。

## 四、实现步骤

### 第一步：环境准备与配置

1. 创建 `.env` 文件，配置模型路径与 API Key：

```ini
DEEPSEEK_API_KEY=your_deepseek_api_key
WEIGHTS_PATH=./yolov8n.pt
YOLO_CONF_THRESHOLD=0.15
```
2. 安装依赖库：
```
pip install -r requirements.txt
```

3. 添加训练后的模型（例如 `yolov8n.pt`），并放置于项目根目录或指定路径。

### 第二步：图像识别模块实现（`yolo_v8.py`）

实现 YOLOv8 的封装类 `YoloV8Detector`，用于从图像字节流中解码图像，并进行目标检测。支持返回识别后的图像及标签集合。主要函数包括：

- `_get_image_from_chunked`：图像解码与格式转换
    
- `detect_frame`：目标检测
    
- `plot_results`：绘制识别结果与提取标签
    

调用方式如下：
```python
detector = YoloV8Detector(chunked=image_bytes)
frame, labels = await detector()

```
### 第三步：大语言模型问答模块实现（`deepseek.py`）

封装 DeepSeek 流式问答逻辑，使用 OpenAI SDK 连接 DeepSeek 接口，支持用户多轮会话。关键逻辑包括：

- 用户问题与上下文整合
    
- 调用 `client.chat.completions.create` 接口
    
- 异步生成器 `stream_deepseek` 实现流式输出
    
- 会话信息保存至 `sessions` 字典，按用户维度记录上下文
    

提供 API 路由 `/deepseek/ask` 接收请求并返回流式回答。

---

### 第四步：主应用整合与路由注册（`main.py`）

整合上述两个模块，构建完整 FastAPI 应用接口：
```python
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from deepseek import deepseek_router
from yolo_v8 import YoloV8Detector

app = FastAPI()

app.include_router(deepseek_router)

@app.post("/detect")
async def detect_image(file: UploadFile = File(...)):
    bytes_data = await file.read()
    detector = YoloV8Detector(chunked=bytes_data)
    frame, labels = await detector()
    return JSONResponse({"detected_labels": list(labels)})

```
### 第五步：运行与测试

通过以下命令运行项目：

```
python main.py
```

接口功能验证流程如下：

1. 调用 `/detect` 上传图片，返回识别标签（如 `["翠鸟"]`）
    
2. 用户向 `/deepseek/ask` 提交问题，例如：“介绍一下翠鸟”
    
3. 服务端基于上下文调用大语言模型返回答复内容（流式）
    

---

## 五、后续优化建议

- 增加对识别结果图像的 base64 返回，便于前端展示
    
- 加入图像上传压缩策略，提升 YOLO 推理效率
    
- 支持批量识别或多目标筛选
    
- 前端集成图像上传与问答接口，实现完整用户体验
    
- 会话历史管理与持久化（如使用 Redis 或数据库）
    

---

## 六、项目结构

```
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
