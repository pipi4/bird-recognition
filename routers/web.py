from fastapi import APIRouter
from fastapi.responses import FileResponse

web_router = APIRouter(tags=["Web路由"])

# URL path: /
@web_router.get("/")
async def root():
    # 返回 static/index.html
    return FileResponse("static/index.html")
    