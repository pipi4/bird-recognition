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
    CONF_THRESHOLD = float(os.getenv("YOLO_CONF_THRESHOLD", 0.10))

    def __init__(self, chunked: bytes = None):
        """
        初始化YoloV8Detector类。

        参数:
        chunked (bytes): 图像的字节流。
        """
        self._bytes = chunked
        self._device = self._get_device()
        self._model = self._load_model()

    def _get_device(self) -> str:
        """
        获取可用的设备（mps, cuda 或 cpu）。

        返回:
        str: 设备名称。
        """
        if platform.system().lower() == "darwin":
            return "mps"
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"

    def _load_model(self):
        """
        加载YOLOv8模型。

        返回:
        YOLO: 加载的YOLOv8模型。
        """
        model = YOLO(YoloV8Detector.PATH)
        return model

    async def __call__(self):
        """
        处理图像并返回检测结果。

        返回:
        tuple: 包含处理后的图像和检测标签的元组。
        """
        frame = self._get_image_from_chunked()
        results = self.detect_frame(frame)
        frame, labels = self.plot_results(results, frame)
        return frame, set(labels)

    def _get_image_from_chunked(self):
        """
        将字节流转换为图像。

        返回:
        np.ndarray: 图像的numpy数组。
        """
        # 将字节流转换为numpy数组
        arr = np.asarray(bytearray(self._bytes), dtype=np.uint8)
        # 解码图像
        img = cv2.imdecode(arr, -1)
        if img is None:
            print(f"图像解码失败，字节流的前100个字节：{self._bytes[:100]}")
            raise ValueError(f"无法解码图像，接收到的字节流长度为: {len(self._bytes)}")  # 检查字节流是否符合预期

        # 转换为3通道RGB图像
        if img.shape[-1] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        elif len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        return img

    def detect_frame(self, frame):
        """
        对图像进行目标检测。

        参数:
        frame (np.ndarray): 输入的图像帧。

        返回:
        list: 检测结果。
        """
        self._model.to(self._device)
        frame = [frame]
        results = self._model(
            frame,
            conf=YoloV8Detector.CONF_THRESHOLD,
            save_conf=True
        )
        return results

    def plot_results(self, results, frame):
        """
        在图像上绘制检测结果。

        参数:
        results (list): 检测结果。
        frame (np.ndarray): 输入的图像帧。

        返回:
        tuple: 包含绘制结果的图像和检测标签的元组。
        """
        labels = []
        for r in results:
            boxes = r.boxes
            for box in boxes:
                c = box.cls
                l = self._model.names[int(c)]
                labels.append(l)
        frame = results[0].plot()
        return frame, labels
