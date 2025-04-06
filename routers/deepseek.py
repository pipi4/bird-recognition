from fastapi import FastAPI, Request, APIRouter
from fastapi.responses import StreamingResponse  # 增加流式输出
from openai import OpenAI
from dotenv import load_dotenv
import os
import asyncio

# 加载环境变量
load_dotenv(dotenv_path=".env")
API_KEY = os.getenv("DEEPSEEK_API_KEY")

# 如果环境变量没有正确加载，抛出异常
if not API_KEY:
    raise ValueError("DEEPSEEK_API_KEY 环境变量未设置！")

# 创建FastAPI应用实例
app = FastAPI()

# DeepSeek API 客户端
client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

# 用于存储会话信息
sessions = {}

# 创建一个API路由实例，路径前缀为/deepseek，标签为“deepseek大模型”
deepseek_router = APIRouter(tags=["deepseek大模型"], prefix="/deepseek")


# 获取会话（每个用户会话唯一）
def get_session(user_id: str):
    """
    获取指定用户的会话信息，如果会话不存在则创建一个新的会话。

    参数:
    user_id (str): 用户的唯一标识符。

    返回:
    list: 用户的对话历史。
    """
    if user_id not in sessions:
        sessions[user_id] = []
    return sessions[user_id]


# 流式响应生成器
async def stream_deepseek(user_id: str, prompt: str):
    """
    处理用户提问并生成流式响应。

    参数:
    user_id (str): 用户的唯一标识符。
    prompt (str): 用户的提问。

    返回:
    generator: 逐步返回AI回复的生成器。
    """
    # 获取用户的历史对话
    messages = get_session(user_id)
    messages.append({"role": "user", "content": prompt})  # 添加当前用户提问

    # 发送请求，开启流式模式
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        max_tokens=1024,
        temperature=0.7,
        stream=True  # 启用流式输出
    )

    collected_content = ""  # 收集 AI 回复
    for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            text = chunk.choices[0].delta.content
            collected_content += text
            yield text  # 逐步返回给客户端
            await asyncio.sleep(0.05)  # 模拟延迟，优化流式效果

    # 保存 AI 回复到对话历史中
    messages.append({"role": "assistant", "content": collected_content})


# API接口 - 提问
@deepseek_router.post("/ask")
async def ask_question(request: Request):
    """
    处理用户提问并返回流式响应。

    参数:
    request (Request): 包含用户请求的Request对象。

    返回:
    StreamingResponse: 包含AI回复的流式响应。
    """
    data = await request.json()
    user_id = data.get("user_id", "default_user")  # 从请求获取 user_id（确保每个用户有独立会话）
    prompt = data["question"]

    # 返回流式响应
    return StreamingResponse(stream_deepseek(user_id, prompt), media_type="text/plain")


# 注册路由
app.include_router(deepseek_router)
