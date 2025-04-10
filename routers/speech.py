from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import websockets
import json
import hmac
import hashlib
import base64
import asyncio
from datetime import datetime
from time import mktime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time

speech_router = APIRouter()

STATUS_FIRST_FRAME = 0
STATUS_CONTINUE_FRAME = 1
STATUS_LAST_FRAME = 2

class WsParam:
    def __init__(self, APPID, APIKey, APISecret):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret

        self.CommonArgs = {"app_id": self.APPID}
        self.BusinessArgs = {
            "domain": "iat",
            "language": "zh_cn",
            "accent": "mandarin",
            "vinfo": 1,
            "vad_eos": 10000
        }

    def create_url(self):
        url = 'wss://ws-api.xfyun.cn/v2/iat'
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        signature_origin = f"host: ws-api.xfyun.cn\ndate: {date}\nGET /v2/iat HTTP/1.1"
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode()
        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha}"'
        authorization = base64.b64encode(authorization_origin.encode()).decode()
        v = {"authorization": authorization, "date": date, "host": "ws-api.xfyun.cn"}
        return url + '?' + urlencode(v)


@speech_router.websocket("/ws/speech")
async def websocket_speech(websocket: WebSocket):
    await websocket.accept()
    APPID = 'b931f602'
    APIKey = 'bb611ca4fb155d81779960dea5208ed2'
    APISecret = 'YjBhNmJmYmQwZjViZDhlZTRjNzcwMjU5'

    ws_param = WsParam(APPID, APIKey, APISecret)
    ws_url = ws_param.create_url()
    status = STATUS_FIRST_FRAME

    try:
        async with websockets.connect(ws_url) as ws_xf:
            await websocket.send_text("语音识别连接已建立")

            async def recv_from_xf():
                try:
                    async for msg in ws_xf:
                        result_data = json.loads(msg)
                        if "data" in result_data and "result" in result_data["data"]:
                            ws_list = result_data["data"]["result"]["ws"]
                            result_text = ''.join(w["w"] for i in ws_list for w in i["cw"])
                            await websocket.send_text(result_text)
                except Exception as e:
                    await websocket.send_text(f"后端错误：{str(e)}")

            # 启动后台协程监听讯飞返回结果
            asyncio.create_task(recv_from_xf())

            while True:
                audio_chunk = await websocket.receive_bytes()

                if status == STATUS_FIRST_FRAME:
                    d = {
                        "common": ws_param.CommonArgs,
                        "business": ws_param.BusinessArgs,
                        "data": {
                            "status": 0,
                            "format": "audio/L16;rate=16000",
                            "audio": base64.b64encode(audio_chunk).decode(),
                            "encoding": "raw"
                        }
                    }
                    await ws_xf.send(json.dumps(d))
                    status = STATUS_CONTINUE_FRAME
                else:
                    d = {
                        "data": {
                            "status": 1,
                            "format": "audio/L16;rate=16000",
                            "audio": base64.b64encode(audio_chunk).decode(),
                            "encoding": "raw"
                        }
                    }
                    await ws_xf.send(json.dumps(d))

    except WebSocketDisconnect:
        print("前端断开连接")
    except Exception as e:
        print("发生错误：", e)
