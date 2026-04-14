from paddleocr import PaddleOCR
from typing import Dict, List, Optional
import numpy as np
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config


class OCREngine:
    """PaddleOCR 文字识别引擎"""

    def __init__(self, lang: str = "ch", use_gpu: bool = False):
        """
        初始化 OCR 引擎
        Args:
            lang: 识别语言 ("ch" 中文)
            use_gpu: 是否使用 GPU (新版本 PaddleOCR 自动检测)
        """
        os.environ['PADDLE_PDX_LOG_LEVEL'] = 'ERROR'  # 通过环境变量控制日志

        self.ocr = PaddleOCR(
            use_textline_orientation=True,
            lang=lang
        )

    def extract_text(self, image_data) -> Dict:
        """
        从图像中提取文字
        Args:
            image_data: 图像路径 (str) 或 numpy 数组 (np.ndarray)
        Returns:
            Dict 包含：
                - text (str): 所有文本，换行连接
                - confidence (float): 平均置信度
                - boxes (list): 文本框坐标（多边形）
                - lines (list): 每行文本列表
        """
        import cv2
        import tempfile

        # 统一转为临时文件路径（也可直接传数组给 predict，但临时文件方式更稳定）
        if isinstance(image_data, str):
            temp_path = image_data
            need_clean = False
        elif isinstance(image_data, np.ndarray):
            # 确保 BGR 3 通道
            if len(image_data.shape) == 2:
                image_data = cv2.cvtColor(image_data, cv2.COLOR_GRAY2BGR)
            elif len(image_data.shape) == 3 and image_data.shape[2] == 1:
                image_data = cv2.cvtColor(image_data, cv2.COLOR_GRAY2BGR)
            fd, temp_path = tempfile.mkstemp(suffix='.png')
            os.close(fd)
            cv2.imwrite(temp_path, image_data)
            need_clean = True
        else:
            raise TypeError("image_data must be str or np.ndarray")

        try:
            # 新版 API: predict 返回 list of dict
            result = self.ocr.predict(temp_path)
        finally:
            if need_clean and os.path.exists(temp_path):
                os.unlink(temp_path)

        # 解析新版返回格式
        if not result or len(result) == 0:
            return {"text": "", "confidence": 0.0, "boxes": [], "lines": []}

        img_result = result[0]  # 第一张图的结果字典
        texts = img_result.get('rec_texts', [])
        scores = img_result.get('rec_scores', [])
        # 优先使用 rec_polys（识别后文本框），若没有则使用 dt_polys（检测框）
        boxes = img_result.get('rec_polys', img_result.get('dt_polys', []))

        if not texts:
            return {"text": "", "confidence": 0.0, "boxes": [], "lines": []}

        avg_conf = sum(scores) / len(scores) if scores else 0.0

        return {
            "text": "\n".join(texts),
            "confidence": avg_conf,
            "boxes": boxes,
            "lines": texts
        }

if __name__ == "__main__":
    if __name__ == "__main__":
        TEST_IMAGE_PATH = r"C:\Users\32601\.openclaw\workspace\.worktrees\auto-grading\auto-grading-system\tests\img_0005.jpg"
        ocr_engine = OCREngine(lang='ch')
        result = ocr_engine.extract_text(TEST_IMAGE_PATH)
        print("识别文本:\n", result['text'])
        print("平均置信度:", result['confidence'])
        print("每行文本:", result['lines'])
