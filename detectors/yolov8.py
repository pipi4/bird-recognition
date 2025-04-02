import torch
import numpy as np
import cv2
import os
import platform
from ultralytics import YOLO
from dotenv import load_dotenv

class YoloV8Detector:
    # 加载环境变量
    load_dotenv(dotenv_path=".env")
    PATH = os.getenv("WEIGHTS_PATH")
    # 置信度阈值
    CONF_THERESHOLD = os.getenv("YOLO_CONF_THRESHOLD", 0.10)

    def __init__(self, chunked: bytes = None):
        self._bytes = chunked
        self._device = self._get_device()
        self._model = self._load_model()

    def _get_device(self) -> str:
        if platform.system().lower == "darwin":
            return "mps"
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"

    def _load_model(self):
        model = YOLO(YoloV8Detector.PATH)
        return model
        
    async def __call__(self):
        """
        __call__在实例化对象后被调用
        处理图像并返回检测结果
        """
        frame = self._get_image_from_chunked()
        results = self.detect_frame(frame)
        frame, labels = self.plot_results(results, frame)
        return frame, set(labels)

    def _get_image_from_chunked(self):
        # 将字节流转换为numpy数组
        arr = np.asarray(bytearray(self._bytes), dtype=np.uint8)
        # 解码图像
        img = cv2.imdecode(arr, -1)
        if img is None:
            raise ValueError("无法解码图像")

        # 转换为3通道RGB图像
        if img.shape[-1] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        elif len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        return img

    def detect_frame(self, frame):
        """
        对图像进行目标检测
        """
        self._model.to(self._device)
        frame = [frame]
        results = self._model(
            frame,
            conf=YoloV8Detector.CONF_THERESHOLD,
            save_conf=True
        )
        return results

    def plot_results(self, results, frame):
        for r in results:
            boxes = r.boxes
            labels = []
            for box in boxes:
                c = box.cls
                l = self._model.names[int(c)]
                labels.append(l)
        frame = results[0].plot()
        return frame, labels