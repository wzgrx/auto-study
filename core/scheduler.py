"""
18 — 调度引擎
步进 / 全自动 / 定时三种模式
"""
from __future__ import annotations
import logging
from core.tab_manager import TabManager
from core.config import Config
from core.login import UniversalLogin
from core.scanner import CourseScanner
from core.player import VideoPlayer
from core.progress import ProgressManager
from core.reporter import Reporter
from core.health import HealthMonitor
from core.persistence import SessionManager
from core.brain import BrowserBrain
from core.plugin import PluginRegistry

logger = logging.getLogger("scheduler")


class Scheduler:
    """任务调度器"""

    def __init__(self):
        self.tm = TabManager()
        self.brain = BrowserBrain(self.tm)
        self.persist = SessionManager()
        self.login = UniversalLogin(self.brain, self.persist)
        self.scanner = CourseScanner(self.brain)
        self.player = VideoPlayer(self.brain)
        self.progress = ProgressManager()
        self.reporter = Reporter()
        self.health = HealthMonitor()

    def auto(self, platform: str):
        """全自动模式"""
        logger.info(f"===== 开始全自动刷课: {platform} =====")
        account = Config.get_account(platform)
        plugin = PluginRegistry.get(platform)

        # 获取一个标签页（不新建，复用已有的）
        tab = self.tm.get()
        logger.info(f"使用标签页: {tab.tab_id[:16] if tab.tab_id else '?'}")

        # 登录
        if account and plugin:
            self.login.login(
                tab, plugin.login_url,
                account["user"], account["pass"],
                plugin.login_selectors, plugin)

        # 扫描课程
        courses = self.scanner.scan(tab)
        if not courses:
            logger.info("没有需要刷的课程")
            return

        # 逐个播放
        for i, course in enumerate(courses):
            self.health.heartbeat()
            ok = self.player.play(tab, course)
            self.progress.save(course.id or str(i), 100 if ok else 0,
                               "完成" if ok else "失败")
            self.reporter.progress(i + 1, len(courses), course.name)

        # 报告
        self.reporter.summary(self.progress.stats())
        logger.info("===== 刷课完毕 =====")

    def step(self, step_name: str):
        """步进模式"""
        logger.info(f"步进执行: {step_name}")

    def cron(self, platform: str, expr: str):
        """定时模式"""
        logger.info(f"定时任务注册: {platform} @ {expr}")
