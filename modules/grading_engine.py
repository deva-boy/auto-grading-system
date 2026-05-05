from typing import Dict, List
import json

from sympy import false
from zai import ZhipuAiClient

class GradingEngine:
    """评分引擎：每个大题直接给出总分，不拆分小题分数，理由固定写死"""

    def __init__(self, use_ai: bool = True):
        self.use_ai = use_ai
        self.client = ZhipuAiClient(api_key="VLM_API_KEY")

    # ------------------- 新增：整体大题评分（无理由，只返回整数分数）-------------------
    def _ai_grade_big_question(self, big_question_desc: str, student_answer: str, total_score: int) -> int:
        """
        对一个大题进行整体评分（将大题中所有子题的题目和参考答案拼接后一次性发送）
        返回值：整数得分（0 ~ total_score）
        """
        prompt = f"""请根据以下大题信息进行评分：
【大题完整内容】{big_question_desc}
【学生答案】{student_answer}
【满分】{total_score}

评分要求：
- 只输出一个 JSON 对象，格式为 {{"score": 整数分数}}
- 不要输出任何其他内容（包括理由、解释等）
- 分数必须是不超过满分的非负整数
"""
        try:
            response = self.client.chat.completions.create(
                model="glm-4.7",
                messages=[
                    {"role": "system", "content": "你是一位严格的试卷评分专家，只返回 JSON 格式的分数，不包含理由。输出示例：{\"score\": 8}"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            score = int(result.get("score", 0))
            # 边界修正
            if score < 0:
                score = 0
            if score > total_score:
                score = total_score
            return score
        except Exception as e:
            print(f"AI 大题评分异常: {e}")
            return 0

    # ------------------- 核心修改：grade_side 按大题整体评分，返回每个大题的总分 -------------------
    def grade_side(self, big_questions, student_text, start_big_index, grading_engine):
        """
        对一面试卷进行评分（正面或反面），每个大题直接返回一个总分（不再拆分子题分数）

        参数:
            big_questions: 标准答案中的大题列表（每个元素包含 title, sub_questions 等）
            student_text:  学生该面试卷的 OCR 文本（整面）
            start_big_index: 起始大题索引（正面从1开始，反面从3开始）
            grading_engine: 保留参数，未使用（兼容旧调用）

        返回值:
            grading: dict, 格式如 {"big_1": {"score": 25, "reason": "AI 评分完成"}, ...}
            total:   int,   该面所有大题得分之和
        """
        grading = {}
        total = 0

        for i, big_q in enumerate(big_questions):
            # 实际大题编号（如1,2,3,4）
            actual_index = start_big_index + i
            sub_questions = big_q.get("sub_questions", [])
            if not sub_questions:
                continue

            # 拼接该大题所有子题的题目和参考答案（形成一个完整的大题描述）
            big_question_desc = ""
            max_score_for_big = 0
            for sq in sub_questions:
                q_text = sq.get("question", "")
                a_text = sq.get("answer", "")
                sub_score = sq.get("score", 0)
                big_question_desc += f"【子题 {sq['id']}】\n题目：{q_text}\n参考答案：{a_text}\n本题满分：{sub_score}分\n\n"
                max_score_for_big += sub_score

            # 调用 AI 获取该大题的得分（一次请求）
            big_score = self._ai_grade_big_question(
                big_question_desc=big_question_desc,
                student_answer=student_text,
                total_score=max_score_for_big
            )

            # 存储该大题的评分结果（键名如 "big_1"）
            q_id = f"big_{actual_index}"
            grading[q_id] = {
                "score": big_score,
                "reason": "AI 评分完成"
            }
            total += big_score

        return grading, total

if __name__ == "__main__":
    import json
    from grading_engine import GradingEngine  # 根据实际路径修改

    # 1. 加载标准答案配置（只取前两个大题用于测试）
    with open("../answer_config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    big_questions = config["big_questions"][:2]  # 只测试第一、二大题

    # 2. 模拟学生答案（实际应用中应为 OCR 识别的文本）
    fake_student_answer = """
    （1）电梯控制系统应该设计成硬实时系统，因为异常情况需要及时响应。
    轮询和前后台可以混合使用，例如自动进样器主流程用轮询，通讯用中断。
    裸机下直接写寄存器，Linux下需要写驱动。
    计数器初始值应设为64536。
    scanf会触发系统调用，从用户模式切换到管理模式，然后返回。
    对于串口问题，可能是因为发送太快，需要加入延时或检查TI标志。
    AD转换需要16位，存储需要Flash，容量大约53MB。
    """
    # 3. 创建评分引擎
    engine = GradingEngine()

    # 4. 调用 grade_side（模拟正面，大题从1开始）
    grading, total = engine.grade_side(big_questions, fake_student_answer, start_big_index=1, grading_engine=None)

    # 5. 输出结果
    print("=== 评分结果 ===")
    for q_id, info in grading.items():
        print(f"{q_id}: 得分 {info['score']} 分，理由: {info['reason']}")
    print(f"\n该面总分: {total} / {sum(bq.get('total_score',0) for bq in big_questions)}")

    """=== 评分结果 ===
    big_1: 得分 21 分，理由: AI 评分完成
    big_2: 得分 20 分，理由: AI 评分完成
    
    该面总分: 41 / 55"""
