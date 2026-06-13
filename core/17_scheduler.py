"""
17 - 调度引擎
步进 / 全自动 / 定时三种模式
"""
from __future__ import annotations
import logging
from core.brain import BrowserBrain
from core.login import UniversalLogin
from core.scanner import CourseScanner
from core.player import VideoPlayer
from core.progress import ProgressManager
from core.reporter import Reporter
from core.health import HealthMonitor

logger = logging.getLogger("scheduler")


class Scheduler:
    """任务调度器"""

    def __init__(self):
        self.brain = BrowserBrain()
        self.login = UniversalLogin(self.brain)
        self.scanner = CourseScanner(self.brain)
        self.player = VideoPlayer(self.brain)
        self.progress = ProgressManager()
        self.reporter = Reporter()
        self.health = HealthMonitor()

    def auto(self, platform: str, username: str, password: str):
        """全自动模式"""
        logger.info(f"开始全自动刷课: {platform}")
        # 登录
        self.login.login(f"https://{platform}", username, password)
        # 扫描课程
        tab = self.brain.get_tab(1)
        courses = self.scanner.scan(tab)
        # 逐个播放
        for course in courses:
            self.health.heartbeat()
            self.player.play(tab, course)
            self.progress.save(course.id, 100)
            self.reporter.progress(
                courses.index(course) + 1, len(courses), course.name)
        self.reporter.summary({"total": len(courses), "completed": len(courses),
                               "success_rate": 100, "duration": "完成"})

    def step(self, step_name: str):
        """步进模式 — 执行指定步骤"""
        logger.info(f"步进执行: {step_name}")

    def cron(self, platform: str, schedule_expr: str):
        """定时模式 — 后台定时运行"""
        logger.info(f"定时任务: {platform} @ {schedule_expr}")
