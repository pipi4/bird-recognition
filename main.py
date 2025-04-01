from fastapi import FastAPI
from uvicorn import Server, Config
from routers.yolo import router
from routers.deepseek import deepseek_router
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

app.include_router(router)
app.include_router(deepseek_router)

# 允许跨域请求（重要！）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def get_index():
    return {"message": "Welcome to the FastAPI application!"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    server = Server(Config(app, host="0.0.0.0", port=port))
    server.run()
