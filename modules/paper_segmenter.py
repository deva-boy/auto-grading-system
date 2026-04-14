import re
import cv2
import numpy as np
from typing import List, Dict, Optional


class PaperSegmenter:
    """试卷结构分割模块"""

    # 大题标题正则模式（使用 Unicode 转义确保括号和逗号正确匹配）
    # \uff08 = 全角左括号（, \uff09 = 全角右括号）, \uff0c = 全角逗号，
    BIG_QUESTION_PATTERN = r".+\uff08共 (\d+) 分\uff0c每小题 (\d+) 分\uff09"

    # 小题号正则模式
    SUB_QUESTION_PATTERN = r"(\d+)\."

    def __init__(self):
        self.big_question_regex = re.compile(self.BIG_QUESTION_PATTERN)
        self.sub_question_regex = re.compile(self.SUB_QUESTION_PATTERN)

    def detect_big_questions(self, image: np.ndarray) -> List[Dict]:
        """
        检测试卷中的大题

        Args:
            image: 预处理后的二值图像

        Returns:
            大题列表，每个包含标题、位置、分数信息
        """
        # 使用 OCR 识别文本位置（简化版：先返回空列表，后续集成 OCR）
        # TODO: 集成 OCR 识别大题标题
        return []

    def parse_score_from_title(self, title: str) -> Optional[Dict]:
        """
        从大题标题解析分数信息

        Args:
            title: 大题标题文本

        Returns:
            分数信息字典，解析失败返回 None
        """
        match = self.big_question_regex.search(title)
        if not match:
            return None

        total_score = int(match.group(1))
        score_per_question = int(match.group(2))

        return {
            "total_score": total_score,
            "sub_question_count": total_score // score_per_question,
            "score_per_question": score_per_question
        }

    def segment_sub_questions(self, image: np.ndarray, big_question_bbox: tuple) -> List[Dict]:
        """
        分割大题内的小题区域

        Args:
            image: 预处理后的图像
            big_question_bbox: 大题区域 (x, y, w, h)

        Returns:
            小题区域列表
        """
        x, y, w, h = big_question_bbox
        roi = image[y:y+h, x:x+w]

        # 查找轮廓
        contours, _ = cv2.findContours(roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        sub_questions = []
        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            if area > 1000:  # 过滤小噪点
                x_offset, y_offset, w_offset, h_offset = cv2.boundingRect(contour)
                sub_questions.append({
                    "id": i + 1,
                    "bbox": (x + x_offset, y + y_offset, w_offset, h_offset)
                })

        return sub_questions

    def get_annotation_position(self, bbox: tuple, position: str = "right") -> tuple:
        """
        计算批注位置

        Args:
            bbox: 答题区域 (x, y, w, h)
            position: 位置类型 ("right", "top_left")

        Returns:
            批注坐标 (x, y)
        """
        x, y, w, h = bbox
        if position == "right":
            return (x + w + 10, y + h // 2)
        elif position == "top_left":
            return (x + 5, y - 5)
        return (x, y)
