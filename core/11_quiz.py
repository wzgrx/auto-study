"""
11 - 答题模块
自动识别并回答章节测验/考试
"""
from __future__ import annotations
import logging
from core.brain import BrowserBrain

logger = logging.getLogger("quiz")


class QuizSolver:
    """自动答题器"""

    def __init__(self, brain: BrowserBrain):
        self.brain = brain

    def solve(self, tab) -> bool:
        """检测并回答当前页面的测验题"""
        if not self._has_quiz(tab):
            return False
        questions = self._extract_questions(tab)
        for q in questions:
            answer = self._lookup_local(q.get("text", ""))
            if not answer:
                answer = self._ask_deepseek(f"题目: {q.get('text')}\n选项: {q.get('options')}\n正确答案是？")
            self._fill_answer(tab, q, answer)
        self.brain.click(tab, "button[type='submit']")
        return True

    def _has_quiz(self, tab) -> bool:
        return "题目" in self.brain.read_text(tab) or "考试" in self.brain.read_text(tab)

    def _extract_questions(self, tab) -> list:
        return []

    def _lookup_local(self, question: str) -> str:
        return ""

    def _ask_deepseek(self, prompt: str) -> str:
        return ""

    def _fill_answer(self, tab, question, answer):
        pass
