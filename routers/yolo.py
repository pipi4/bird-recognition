from fastapi import APIRouter, status, UploadFile, HTTPException, Response
from fastapi.responses import StreamingResponse
from detectors import yolov8
from schemas.yolo import ImageAnalysisResponse, WikipediaInfo, VideoAnalysisResponse
import numpy as np
import cv2
from .wikipeida_api import get_wikipedia_summary  # 引入 Wikipedia API 查询
import os
from typing import List
import asyncio
import json
from database import save_image, get_image, save_video_frame, get_video_frame, save_detection_history, get_detection_history

# 创建一个API路由实例，路径前缀为/yolo，标签为"图像上传和识别"
yolo_router = APIRouter(tags=["图像上传和识别"], prefix="/yolo")

# region upload
# 定义图像上传的POST接口，路径为/yolo/upload
@yolo_router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    responses={201: {"description": "图像上传成功"}},
    response_model=ImageAnalysisResponse,
)
async def yolo_image_upload(file: UploadFile) -> ImageAnalysisResponse:
    """
    处理图像上传请求，使用YOLOv8模型进行图像分析。

    参数:
    file (UploadFile): 上传的图像文件。

    返回:
    ImageAnalysisResponse: 包含图像ID和标签的响应。
    """
    contents = await file.read()  # 读取上传文件的内容
    detector = yolov8.YoloV8Detector(chunked=contents)  # 创建YOLOv8检测器实例
    
    # 获取生成器的第一个（也是唯一一个）结果
    async for frame, labels in detector():
        if frame is None or not isinstance(frame, np.ndarray):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="图像处理失败",
            )

        # Save the image to SQLite database
        image_id = save_image(frame)

        # Save to history
        save_detection_history(
            image_id=image_id,
            detected_objects=list(labels),
            confidence=0.8,  # You might want to get actual confidence from the detector
            has_warning=False  # You might want to implement warning logic
        )

        # 获取第一个识别的鸟类名称（可以扩展成多个）
        if labels:
            bird_name_with_prefix = list(labels)[0]
            # 去掉前缀（假设前缀是类似于 '001.' 的格式）
            bird_name = bird_name_with_prefix.split('.', 1)[-1]
            wiki_info = get_wikipedia_summary(bird_name)

            # 如果没有找到鸟类信息，返回默认的 WikipediaInfo 实例
            if wiki_info.get("title") == "未知":
                wiki_info = WikipediaInfo(
                    title="Unknown Bird",
                    summary="Sorry, no information available.",
                    image=None,
                    wiki_url=f"https://en.wikipedia.org/wiki/Special:Search?search={bird_name}"
                )
        else:
            wiki_info = WikipediaInfo(
                title="No Detection",
                summary="No birds were detected in the image.",
                image=None,
                wiki_url=""
            )

        return ImageAnalysisResponse(
            id=image_id,
            labels=labels,
            wiki_info=wiki_info
        )

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="图像处理失败",
    )

# 定义视频上传的POST接口，路径为/yolo/upload/video
@yolo_router.post(
    "/upload/video",
    status_code=status.HTTP_201_CREATED,
    responses={201: {"description": "视频上传成功"}},
)
async def yolo_video_upload(file: UploadFile):
    """
    处理视频上传请求，使用YOLOv8模型进行视频分析。

    参数:
    file (UploadFile): 上传的视频文件。

    返回:
    StreamingResponse: 流式响应，包含处理后的视频帧和检测结果。
    """
    contents = await file.read()  # 读取上传文件的内容

    async def generate():
        try:
            detector = yolov8.YoloV8Detector(chunked=contents, is_video=True)  # 创建YOLOv8检测器实例
            async for frame, labels in detector():
                # Save the frame to SQLite database
                frame_id = save_video_frame(frame)

                # 创建包含帧和标签的响应
                response = {
                    'frame_id': frame_id,
                    'labels': list(labels)
                }

                # 发送JSON格式的响应
                yield f"data: {json.dumps(response)}\n\n"

        except Exception as e:
            print(f"视频处理错误: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST",
            "Access-Control-Allow-Headers": "Content-Type"
        }
    )

# endregion

# region download
# 定义图像下载的GET接口，路径为/yolo/download/{image_id}
@yolo_router.get(
    "/download/{image_id}",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "图像下载成功",
            "content": {"image/png": {}},
        },
        404: {
            "description": "图像未找到",
        },
    },
    response_class=Response,
)
async def yolo_image_download(image_id: int) -> Response:
    """
    处理图像下载请求，返回指定ID的图像。

    参数:
    image_id (int): 图像的唯一标识符。

    返回:
    Response: 包含图像数据的响应。
    """
    image = get_image(image_id)
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图像未找到",
        )
    
    success, encoded_image = cv2.imencode(".png", image)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="图像编码失败",
        )
    
    return Response(content=encoded_image.tobytes(), media_type="image/png")

# 定义视频帧下载的GET接口，路径为/yolo/download/video/{frame_id}
@yolo_router.get(
    "/download/video/{frame_id}",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "视频帧下载成功",
            "content": {"image/png": {}},
        },
        404: {
            "description": "视频帧未找到",
        },
    },
    response_class=Response,
)
async def yolo_video_frame_download(frame_id: int) -> Response:
    """
    处理视频帧下载请求，返回指定ID的视频帧。

    参数:
    frame_id (int): 视频帧的唯一标识符。

    返回:
    Response: 包含视频帧数据的响应。
    """
    frame = get_video_frame(frame_id)
    if frame is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="视频帧未找到",
        )
    
    success, encoded_frame = cv2.imencode(".png", frame)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="视频帧编码失败",
        )
    
    return Response(content=encoded_frame.tobytes(), media_type="image/png")
# endregion

# region history
@yolo_router.get(
    "/history",
    status_code=status.HTTP_200_OK,
    responses={200: {"description": "成功获取历史记录"}},
)
async def get_history(limit: int = 50):
    """
    获取检测历史记录。
    
    参数:
    limit (int): 返回的记录数量限制，默认为50
    
    返回:
    List[dict]: 历史记录列表
    """
    history = get_detection_history(limit)
    return history
# endregion
