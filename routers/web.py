from fastapi import APIRouter
from fastapi.responses import FileResponse

# 创建一个API路由实例，标签为“Web路由”
web_router = APIRouter(tags=["Web路由"])

# 定义根路径的GET接口，路径为/
@web_router.get("/")
async def root():
    """
    返回静态文件 static/index.html。

    返回:
    FileResponse: 包含 static/index.html 文件的响应。
    """
    # 返回 static/index.html
    return FileResponse("static/index.html")
