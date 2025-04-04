from fastapi import APIRouter, status, UploadFile, HTTPException, Response
from detectors import yolov8
from schemas.yolo import ImageAnalysisResponse, WikipediaInfo
import numpy as np
import cv2
from .wikipeida_api import get_wikipedia_summary  # 引入 Wikipedia API 查询

# 创建一个API路由实例，路径前缀为/yolo，标签为“图像上传和识别”
yolo_router = APIRouter(tags=["图像上传和识别"], prefix="/yolo")

# 内存中存储上传的图像
images = []

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
    frame, labels = await detector()  # 进行图像检测

    if frame is None or not isinstance(frame, np.ndarray):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="图像处理失败",
        )

    success, encoded_image = cv2.imencode(".png", frame)  # 将图像编码为PNG格式

    if not success:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="图像编码失败",
        )

    images.append(encoded_image)  # 将编码后的图像存储在内存中
    # 获取第一个识别的鸟类名称（可以扩展成多个）
    bird_name_with_prefix = list(labels)[0]
    # 去掉前缀（假设前缀是类似于 '001.' 的格式）
    bird_name = bird_name_with_prefix.split('.', 1)[-1]  # 以 '.' 为分隔符，取第二部分，即去掉数字和点
    wiki_info = get_wikipedia_summary(bird_name)

    # 如果没有找到鸟类信息，返回默认的 WikipediaInfo 实例
    if wiki_info.get("title") == "未知":
        wiki_info = WikipediaInfo(
            title="Unknown Bird",
            summary="Sorry, no information available.",
            image=None,
            wiki_url=f"https://en.wikipedia.org/wiki/Special:Search?search={bird_name}"
        )

    return ImageAnalysisResponse(
        id=len(images),
        labels=labels,
        wiki_info=wiki_info
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
    try:
        # 返回指定ID的图像
        return Response(content=images[image_id - 1].tobytes(), media_type="image/png")
    except IndexError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图像未找到",
        )
# endregion
