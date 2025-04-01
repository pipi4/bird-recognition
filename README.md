# bird-recognition

## 项目安装

1. 安装依赖项

`pip install -r requirements.txt`

2. 设置YOLO模型的权重路径(默认使用yolov8n)

`export YOLO_WEIGHTS_PATH=path/to/your/weights`

3. 设置置信度阈值(默认0.25)

`export YOLO_CONF_THRESHOLD=0.5`

4. 在项目根路径下创建`.env`文件并设置DEEPSEEK_API_KEY

5. 运行项目

`python main.py`

## API 文档

运行项目后见<http://localhost:8000/docs>
