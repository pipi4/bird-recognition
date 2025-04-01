from fastapi import FastAPI, Request, APIRouter
from dotenv import load_dotenv
import os
import requests

# 加载环境变量
load_dotenv(dotenv_path=".env")
API_KEY = os.getenv("DEEPSEEK_API_KEY")
# 如果环境变量没有正确加载，抛出异常
if not API_KEY:
    raise ValueError("DEEPSEEK_API_KEY 环境变量未设置！")
app = FastAPI()

# URL path: /yolo
deepseek_router = APIRouter(tags=["deepseek大模型"], prefix="/deepseek")

# API接口
@deepseek_router.post("/ask")
async def ask_question(request: Request):
    data = await request.json()
    return {"answer": ask_deepseek(data["question"])}

# DeepSeek API调用函数
def ask_deepseek(prompt: str):
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    data = {
        "model": "deepseek-reasoner",  # 使用R1推理模型
        "messages": [
            {
                "role": "system",
                "content": "你是一位鸟类学专家，精通全球鸟类物种的识别、习性和生态知识。回答需专业且通俗易懂，包含拉丁学名。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.3  # 控制回答严谨性
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()['choices'][0]['message']['content']



