from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import routers.web
import routers.speech  # 导入语音识别的路由模块
import routers.yolo
import routers.llm  # 导入大模型路由模块
from uvicorn import Server, Config
from fastapi.middleware.cors import CORSMiddleware
import os

# 创建FastAPI应用实例
app = FastAPI()

# 注册路由
app.include_router(routers.speech.speech_router)  # 注册语音识别路由
app.include_router(routers.yolo.yolo_router)  # 注册YOLO路由
app.include_router(routers.web.web_router)  # 注册Web路由
app.include_router(routers.llm.llm_router)  # 注册大模型路由

# 挂载静态文件目录
app.mount(
    "/static",  # 挂载路径
    StaticFiles(directory="static"),  # 静态文件目录
    name="static",  # 名称
)

# 添加CORS中间件以允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,  # 允许发送凭据
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有HTTP头
)

# 应用主程序入口
if __name__ == "__main__":
    # 从环境变量获取端口号，默认为8000
    port = int(os.environ.get("PORT", 8000))
    # 创建并运行Uvicorn服务器
    server = Server(Config(app, host="127.0.0.1", port=port))
    server.run()
