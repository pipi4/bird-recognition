# bird-recognition

## 项目安装

`pip install -r requirements.txt`

## 配置环境变量

1. 在项目根路径下创建`.env`文件

2. 设置YOLO模型的权重路径(默认使用yolov8n)

`WEIGHTS_PATH=path/to/your/weights`

3. 设置置信度阈值(默认0.25)

`YOLO_CONF_THRESHOLD=0.5`

4. 设置deepseek的api

`DEEPSEEK_API_KEY=your_api_key`

## 运行项目

`python main.py`

## API 文档

运行项目后见<http://localhost:8000/docs>
