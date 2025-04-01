from fastapi import APIRouter
from fastapi.responses import FileResponse
from pathlib import Path

web_router = APIRouter(tags=["Web路由"])

# 获取根目录下 static 文件夹的路径
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

# URL path: /
@web_router.get("/")
async def root():
    # 返回 static/index.html
    return FileResponse(STATIC_DIR / "index.html")
    