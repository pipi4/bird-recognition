from fastapi import APIRouter, status, UploadFile, HTTPException, Response
from fastapi.responses import StreamingResponse
from detectors import yolov8
from schemas.yolo import ImageAnalysisResponse, WikipediaInfo, VideoAnalysisResponse
import numpy as np
import cv2
from .wikipeida_api import get_wikipedia_summary  # 引入 Wikipedia API 查询
import os
from typing import List, Dict
import asyncio
import json
from database import save_image, get_image, save_video_frame, get_video_frame, save_detection_history, get_detection_history, save_qa_interaction, get_qa_count, save_alert, get_alert_counts, get_species_alert_stats
from datetime import datetime, timedelta
import sqlite3

# 创建一个API路由实例，路径前缀为/yolo，标签为"图像上传和识别"
yolo_router = APIRouter(tags=["图像上传和识别"], prefix="/yolo")

# region 图像上传
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
# endregion

# region 视频上传
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
        # 使用了 Server-Sent Events (SSE) 技术（text/event-stream）
        # 每检测完一帧就立即返回该帧的结果，不等待整个视频处理完成
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

# region 图像下载
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
# endregion

# region 视频帧下载
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

# region 历史记录
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

# region 统计数据
@yolo_router.get(
    "/stats",
    status_code=status.HTTP_200_OK,
    responses={200: {"description": "成功获取统计数据"}},
)
async def get_stats():
    """
    获取统计数据，包括总识别数、当日识别数、预警数等。
    
    返回:
    Dict: 包含各项统计数据的字典
    """
    # 引用数据库路径
    DB_PATH = "yolo_data.db"
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 获取总识别数
    cursor.execute("SELECT COUNT(*) FROM detection_history")
    total_count = cursor.fetchone()[0]
    
    # 获取当日识别数
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute(
        "SELECT COUNT(*) FROM detection_history WHERE date(created_at) = ?", 
        (today,)
    )
    today_count = cursor.fetchone()[0]
    
    # 获取总预警数
    cursor.execute("SELECT COUNT(*) FROM detection_history WHERE has_warning = 1")
    warnings_count = cursor.fetchone()[0]
    
    # 获取当日预警数
    cursor.execute(
        "SELECT COUNT(*) FROM detection_history WHERE has_warning = 1 AND date(created_at) = ?", 
        (today,)
    )
    today_warnings_count = cursor.fetchone()[0]
    
    # 获取近7天的识别趋势
    trend_data = []
    for i in range(6, -1, -1):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        next_date = (datetime.now() - timedelta(days=i-1)).strftime('%Y-%m-%d') if i > 0 else (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        cursor.execute(
            "SELECT COUNT(*) FROM detection_history WHERE date(created_at) >= ? AND date(created_at) < ?",
            (date, next_date)
        )
        count = cursor.fetchone()[0]
        
        # 将日期格式化为月/日
        display_date = (datetime.now() - timedelta(days=i)).strftime('%m/%d')
        
        trend_data.append({
            "date": display_date,
            "count": count
        })
    
    # 打印日志，便于调试
    print(f"趋势数据: {trend_data}")
    
    conn.close()
    
    # 获取问答次数
    qa_count = get_qa_count()
    
    # 获取今日问答次数
    today_qa_count = get_qa_count(today)
    
    # 从species_alerts表获取预警统计数据
    alert_counts = get_alert_counts()
    
    # 替换原有的预警计数方式
    warnings_count = alert_counts["total"]
    today_warnings_count = alert_counts["today"]
    
    # 构建返回数据
    result = {
        "total": total_count,
        "today": today_count,
        "warnings": warnings_count,
        "today_warnings": today_warnings_count,
        "qa_count": qa_count,
        "today_qa_count": today_qa_count,
        "detection_trend": trend_data,
        "species_stats": get_species_alert_stats()  # 添加物种预警统计
    }
    
    # 打印返回数据，便于调试
    print(f"Stats API 返回数据: {result}")
    
    return result

# region 问答交互
# 保存问答交互记录
@yolo_router.post(
    "/qa",
    status_code=status.HTTP_201_CREATED,
    responses={201: {"description": "问答记录保存成功"}},
)
async def save_qa(data: dict):
    """
    保存问答交互记录。
    
    参数:
    data (dict): 包含问题和回答的字典
    
    返回:
    dict: 操作结果
    """
    question = data.get("question")
    answer = data.get("answer")
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="问题不能为空",
        )
    
    qa_id = save_qa_interaction(question, answer)
    
    return {
        "id": qa_id,
        "message": "问答记录保存成功",
        "success": True
    }
# endregion

# region 预警
# 保存物种预警
@yolo_router.post(
    "/alert",
    status_code=status.HTTP_201_CREATED,
    responses={201: {"description": "预警保存成功"}},
)
async def save_species_alert(data: dict):
    """
    保存物种预警记录。
    
    参数:
    data (dict): 包含预警信息的字典
    
    返回:
    dict: 操作结果
    """
    message = data.get("message", "")
    species = data.get("species", "")
    timestamp = data.get("timestamp", datetime.now().isoformat())
    
    if not species:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="物种名称不能为空",
        )
    
    alert_id = save_alert(message, species)
    
    return {
        "id": alert_id,
        "message": "预警保存成功",
        "success": True
    }
# endregion
