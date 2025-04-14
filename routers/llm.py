from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse, JSONResponse
import httpx
import os
import logging
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建路由器
llm_router = APIRouter(prefix="/api/llm", tags=["llm"])

# 设置Ollama API地址
OLLAMA_API_URL = os.environ.get("OLLAMA_API_URL", "http://localhost:11434")

@llm_router.post("/generate")
async def generate(request: Request):
    """
    代理转发到Ollama API
    """
    try:
        # 读取原始请求内容
        body = await request.json()
        
        # 创建异步HTTP客户端
        async with httpx.AsyncClient() as client:
            try:
                # 转发请求到Ollama API
                response = await client.post(
                    f"{OLLAMA_API_URL}/api/generate",
                    json=body,
                    timeout=60.0
                )
                
                if not response.is_success:
                    logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                    return JSONResponse(
                        status_code=response.status_code,
                        content={"error": f"Ollama API error: {response.status_code}"}
                    )
                
                # 创建流式响应
                async def response_stream():
                    try:
                        async for line in response.aiter_lines():
                            if line:
                                yield f"data: {line}\n\n"
                    except httpx.StreamClosed:
                        logger.warning("Stream was closed")
                    except Exception as e:
                        logger.error(f"Error in stream: {str(e)}")
                        yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
                
                # 返回流式响应
                return StreamingResponse(
                    response_stream(),
                    media_type="text/event-stream"
                )
                
            except httpx.ConnectError:
                logger.error(f"Connection error to Ollama API at {OLLAMA_API_URL}")
                return JSONResponse(
                    status_code=503,
                    content={"error": "Could not connect to language model server"}
                )
                
    except Exception as e:
        logger.exception("Unexpected error in LLM router")
        return JSONResponse(
            status_code=500,
            content={"error": f"Internal server error: {str(e)}"}
        ) 