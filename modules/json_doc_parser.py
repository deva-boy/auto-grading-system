import json
from typing import Dict, List


class JSONDocParser:
    """JSON 配置文件解析器"""

    def __init__(self, config_path: str):
        """
        Args:
            config_path: JSON 配置文件路径
        """
        self.config_path = config_path

    def parse(self) -> Dict:
        """
        解析 JSON 配置文件

        Returns:
            结构化答案数据
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 转换格式以匹配 DocParser 的输出
            big_questions = []
            for big_q in data.get("big_questions", []):
                sub_questions = []
                for sub_q in big_q.get("sub_questions", []):
                    sub_questions.append({
                        "id": sub_q["id"],
                        "question": sub_q["question"],
                        "answer": sub_q["answer"],
                        "score": sub_q["score"]
                    })

                big_questions.append({
                    "index": big_q["index"],
                    "title": big_q["title"],
                    "total_score": big_q["total_score"],
                    "sub_questions": sub_questions
                })

            return {"big_questions": big_questions}

        except Exception as e:
            print(f"JSON 解析失败: {e}")
            return {"big_questions": []}