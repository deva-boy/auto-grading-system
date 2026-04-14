from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2
import config
from typing import Dict, List, Tuple, Optional
from datetime import datetime


class AnnotationRenderer:
    """批注渲染器：在图片上叠加总分和大题得分（不再渲染每个小题的分数）"""

    def __init__(self):
        self.color = tuple(reversed(config.ANNOTATION_COLOR))  # RGB -> BGR
        self.sub_font_size = config.SUB_QUESTION_FONT_SIZE
        self.big_font_size = config.BIG_QUESTION_FONT_SIZE
        self.total_font_size = self.big_font_size + 4

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        """获取字体"""
        try:
            return ImageFont.truetype(config.FONT_PATH, size)
        except:
            return ImageFont.load_default()

    def draw_text_pil(self, image: np.ndarray, position: Tuple[int, int], text: str,
                      font_size: int, color_rgb: Tuple[int, int, int]) -> np.ndarray:
        """
        使用 Pillow 绘制文本（支持换行）
        """
        img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        draw = ImageDraw.Draw(pil_img)
        font = self._get_font(font_size)

        lines = text.split('\n')
        y_offset = position[1]
        line_height = font_size + 4
        for line in lines:
            draw.text((position[0], y_offset), line, fill=color_rgb, font=font)
            y_offset += line_height

        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    def render_total_score(self, image: np.ndarray, total_score: float,
                           position: Tuple[int, int] = (50, 50)) -> np.ndarray:
        """
        绘制科目总成绩
        """
        total_text = f"科目总成绩：{total_score:.1f} 分"
        return self.draw_text_pil(image, position, total_text,
                                  self.total_font_size,
                                  config.ANNOTATION_COLOR)

    def render_big_question_score(self, image: np.ndarray,
                                  question_title: str,
                                  score: float,
                                  position: Tuple[int, int],
                                  reviewer: str = "马兴录") -> np.ndarray:
        """
        在大题标题旁边绘制该大题得分及评阅人、时间
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text = f"{question_title}：{score:.2f} 分\n评阅人：{reviewer} {current_time}"
        return self.draw_text_pil(image, position, text,
                                  self.big_font_size,
                                  config.ANNOTATION_COLOR)

    def render(self, original_image: np.ndarray,
               grading_result: Dict,
               total_score_position: Tuple[int, int] = (50, 50),
               big_question_boxes: Optional[List[Tuple[int, int, int, int]]] = None,
               big_question_titles: Optional[List[str]] = None,
               big_question_scores: Optional[List[float]] = None) -> np.ndarray:
        """
        渲染完整批注结果

        新功能：
          - 自动计算总分（累加 grading_result 中每一项的 score）
          - 在 total_score_position 处显示总分
          - 如果提供了三大列表，则在每个大题标题旁渲染得分（含评阅人时间）

        注意：不再绘制每个小题的分数框

        Args:
            original_image: BGR 图像
            grading_result: 字典，如 {'q_1_1': {'score': 2, 'bbox': ...}, ...}
            total_score_position: 总分显示位置 (x, y)
            big_question_boxes: 每个大题标题的边界框 [(x1,y1,x2,y2), ...] 或 [(x,y,w,h), ...]
            big_question_titles: 对应的标题文本，如 ["一、理解题", "二、简答题"]
            big_question_scores: 对应的大题得分，如 [24.0, 22.0]
        Returns:
            渲染后的 BGR 图像
        """
        result = original_image.copy()

        # 1. 计算总分（累加所有 score）
        total_score = sum(item.get('score', 0) for item in grading_result.values())
        # 2. 渲染总分
        result = self.render_total_score(result, total_score, total_score_position)

        # 3. 渲染大题得分（若提供）
        if big_question_boxes and big_question_titles and big_question_scores:
            if len(big_question_boxes) == len(big_question_titles) == len(big_question_scores):
                for box, title, score in zip(big_question_boxes, big_question_titles, big_question_scores):
                    if not (isinstance(box, (tuple, list)) and len(box) == 4):
                        raise ValueError(f"每个大题框应为包含4个整数的元组，但得到 {box}")
                    x1, y1, x2, y2 = map(int, box)  # 转换为整数
                    # 可选：确保 x2>x1, y2>y1，如果不是则警告并交换
                    if x2 <= x1 or y2 <= y1:
                        print(f"警告：边界框无效 {box}，使用左上角 ({x1},{y1})")
                    # 在标题右侧偏移 20 像素处绘制
                    pos = (x1 + 20, y1)
                    result = self.render_big_question_score(result, title, score, pos)
            else:
                print("警告：大题框数量与标题/得分数量不一致，跳过渲染大题得分")

        return result

    def save(self, image: np.ndarray, output_path: str):
        """保存图片"""
        cv2.imwrite(output_path, image)