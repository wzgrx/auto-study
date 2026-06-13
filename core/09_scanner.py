"""
09 - 课程识别层
自动识别哪些课程需要刷
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from core.brain import BrowserBrain

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

    def __init__(self, brain: BrowserBrain):
        self.brain = brain

    def scan(self, tab) -> list[Course]:
        """扫描当前页面上的所有课程"""
        text = self.brain.read_text(tab)
        vision = self.brain.analyze_screenshot(tab, "列出所有课程及其进度")
        logger.info(f"扫描到页面文字: {text[:200]}")
        logger.info(f"视觉分析: {vision[:200]}")
        return []

    def find_entry(self, tab, course: Course) -> str:
        """找到进入课程学习的入口"""
        return self.brain.analyze_screenshot(tab, f"要进入'{course.name}'，应该点击哪里？")
