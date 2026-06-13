"""
12 — 答题模块
自动识别并回答章节测验/考试
"""
from __future__ import annotations
import logging
from core.config import Config
from core.exceptions import QuizError

logger = logging.getLogger("quiz")


class QuizSolver:
    """自动答题器"""

    def __init__(self, brain):
        self.brain = brain

    def solve(self, tab) -> bool:
        if not self._detect(tab):
            return False
        questions = self._extract(tab)
        for q in questions:
            ans = self._deepseek(q.get("text", ""), q.get("options", ""))
            self._fill(tab, q, ans)
        if Config.QUIZ_ENABLED:
            self.brain.click(tab, "button[type='submit']")
        return True

    def _detect(self, tab) -> bool:
        text = self.brain.read_text(tab)
        return "题目" in text or "考试" in text or "单选" in text

    def _extract(self, tab) -> list[dict]:
        text = self.brain.read_text(tab)
        questions = []
        for line in text.split("\n"):
            if "?" in line or "？" in line:
                questions.append({"text": line.strip(), "options": ""})
        return questions

    def _deepseek(self, question: str, options: str) -> str:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=Config.DEEPSEEK_API_KEY,
                            base_url="https://api.deepseek.com")
            resp = client.chat.completions.create(
                model=Config.DEEPSEEK_MODEL,
                messages=[{"role": "user",
                           "content": f"题目: {question}\n选项: {options}\n请直接输出正确答案"}],
                max_tokens=100)
            return resp.choices[0].message.content or ""
        except Exception as e:
            logger.warning(f"AI 答题失败: {e}")
            return ""

    def _fill(self, tab, question: dict, answer: str):
        if not answer:
            return
        self.brain.execute_js(tab, f"""
        var els = document.querySelectorAll('input,label,textarea');
        for(var e of els){{
            var t=e.textContent||e.value||'';
            if(t.includes('{answer[:20]}')){{e.click();e.focus();break;}}
        }}
        """)
