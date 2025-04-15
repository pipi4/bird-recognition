from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse, JSONResponse
import httpx
import os
import logging
import json
from pydantic import BaseModel

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建路由器
llm_router = APIRouter(prefix="/api/llm", tags=["llm"])

# 设置Ollama API地址
OLLAMA_API_URL = os.environ.get("OLLAMA_API_URL", "http://127.0.0.1:11434")

class TTSRequest(BaseModel):
    text: str

@llm_router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """
    将文本转换为语音
    """
    try:
        # 创建异步HTTP客户端，使用自定义transport禁用代理
        transport = httpx.AsyncHTTPTransport(retries=3)
        async with httpx.AsyncClient(transport=transport) as client:
            # 调用Edge TTS API
            response = await client.post(
                "https://api.edge-tts.com/v1/speak",
                json={
                    "text": request.text,
                    "voice": "zh-CN-XiaoxiaoNeural",
                    "rate": "+0%",
                    "volume": "+0%"
                }
            )
            
            if response.status_code != 200:
                return JSONResponse(
                    status_code=response.status_code,
                    content={"error": "TTS service error"}
                )
                
            # 返回音频数据
            return Response(
                content=response.content,
                media_type="audio/wav"
            )
                
    except Exception as e:
        logger.exception("Error in TTS endpoint")
        return JSONResponse(
            status_code=500,
            content={"error": f"TTS error: {str(e)}"}
        )

@llm_router.post("/generate")
async def generate(request: Request):
    """
    代理转发到Ollama API
    """
    try:
        # 读取原始请求内容
        body = await request.json()
        
        # 创建异步HTTP客户端，使用自定义transport禁用代理
        transport = httpx.AsyncHTTPTransport(retries=3)
        async with httpx.AsyncClient(transport=transport) as client:
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