from docx import Document
from typing import Dict, List, Optional
import re


class DocParser:
    """标准答案 DOCX 文件解析器"""

    # 大题标题正则
    BIG_QUESTION_REGEX = re.compile(r"([一二三四五六七八九十]+)、(.+?)（共 (\d+) 分）")
    # 小题号正则
    SUB_QUESTION_REGEX = re.compile(r"^(\d+)\.")

    def __init__(self):
        pass

    def parse(self, file_path: str) -> Dict:
        """
        解析 DOCX 文件

        Args:
            file_path: DOCX 文件路径

        Returns:
            结构化答案数据
        """
        doc = Document(file_path)

        big_questions = []
        current_big = None
        current_sub = None

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            # 检查是否是大题标题
            big_match = self.BIG_QUESTION_REGEX.match(text)
            if big_match:
                # 保存之前的题目
                if current_big:
                    big_questions.append(current_big)

                current_big = {
                    "index": big_match.group(1),
                    "title": big_match.group(2),
                    "total_score": int(big_match.group(3)),
                    "sub_questions": []
                }
                current_sub = None
                continue

            # 检查是否是小题号
            sub_match = self.SUB_QUESTION_REGEX.match(text)
            if sub_match and current_big:
                # 保存之前的小题
                if current_sub:
                    current_big["sub_questions"].append(current_sub)

                current_sub = {
                    "id": int(sub_match.group(1)),
                    "answer": text[sub_match.end():].strip(),
                    "score": 0  # 需要从大题总分推算
                }
                continue

            # 其他内容作为当前小题的答案补充
            if current_sub:
                current_sub["answer"] += "\n" + text

        # 保存最后一个题目
        if current_sub and current_big:
            current_big["sub_questions"].append(current_sub)
        if current_big:
            big_questions.append(current_big)

        # 计算每题分值
        for big_q in big_questions:
            sub_count = len(big_q["sub_questions"])
            if sub_count > 0:
                score_per = big_q["total_score"] // sub_count
                for sub_q in big_q["sub_questions"]:
                    sub_q["score"] = score_per

        return {"big_questions": big_questions}
