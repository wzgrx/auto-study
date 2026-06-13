"""
10 — 课程识别层
自动识别哪些课程需要刷
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from core.exceptions import CourseScanError, CourseEmptyError

logger = logging.getLogger("scanner")


@dataclass
class Course:
    id: str = ""
    name: str = ""
    progress: float = 0.0
    platform: str = ""
    url: str = ""
    course_type: str = "video"
    metadata: dict = field(default_factory=dict)


class CourseScanner:
    """课程识别器"""

    def __init__(self, brain):
        self.brain = brain

    def scan(self, tab) -> list[Course]:
        try:
            text = self.brain.read_text(tab)
            vision = self.brain.analyze_screenshot(
                tab, "列出所有课程名称、进度百分比、状态")
            logger.info(f"页面文本: {text[:200]}")
            logger.info(f"视觉分析: {vision[:200]}")
            # 返回 AI 识别的课程列表（简化版）
            return self._parse_from_text(text)
        except Exception as e:
            raise CourseScanError(f"课程识别失败: {e}")

    def _parse_from_text(self, text: str) -> list[Course]:
        courses = []
        for line in text.split("\n"):
            if "课程" in line or "课时" in line or "已学" in line or "%" in line:
                courses.append(Course(name=line.strip()[:50], progress=50.0))
        if not courses:
            logger.warning("未识别到课程")
        return courses

    def find_entry(self, tab, course: Course) -> str:
        return self.brain.analyze_screenshot(
            tab, f"要进入课程'{course.name}'学习，应该点击哪里？")
