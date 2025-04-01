from fastapi import APIRouter, status, UploadFile, HTTPException, Response
from detectors import yolov8
from schemas.yolo import ImageAnalysisResponse
import numpy as np
import cv2

# URL path: /yolo
yolo_router = APIRouter(tags=["图像上传和识别"], prefix="/yolo")

# in-memory storage for images
images = []

# region upload
# URL path: /yolo/upload
@yolo_router.post("/upload",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "图像上传成功"},
    },
    response_model=ImageAnalysisResponse,
)

async def yolo_image_upload(file: UploadFile) -> ImageAnalysisResponse:
    contents = await file.read()
    detector = yolov8.YoloV8Detector(chunked=contents)
    frame, labels = await detector()

    if frame is None or not isinstance(frame, np.ndarray):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="图像处理失败",
        )

    success, encoded_image = cv2.imencode(".png", frame)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="图像编码失败",
        )

    images.append(encoded_image)
    return ImageAnalysisResponse(
        id=len(images),
        labels=labels,
    )

# endregion

# region download 
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
    try:
        return Response(content=images[image_id - 1].tobytes(),  media_type="image/png")
    except IndexError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图像未找到",
        )
# endregion