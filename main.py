from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import routers.deepseek
import routers.web
import routers.yolo
from uvicorn import Server, Config
from fastapi.middleware.cors import CORSMiddleware
import routers
import os

app = FastAPI()

# 注册路由
app.include_router(routers.yolo.yolo_router)
app.include_router(routers.deepseek.deepseek_router)
app.include_router(routers.web.web_router)

# 挂载static目录
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)

# 允许跨域请求（重要！）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    server = Server(Config(app, host="127.0.0.1", port=port))
    server.run()
