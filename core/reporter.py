"""
16 - 报告层
进度报告、完成总结
"""
from __future__ import annotations
import logging
from core.notifier import Notifier

logger = logging.getLogger("reporter")


class Reporter:
    """报告器"""

    def __init__(self):
        self.notifier = Notifier()

    def progress(self, done: int, total: int, current: str = ""):
        pct = done / total * 100 if total > 0 else 0
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        msg = f"📊 进度: [{bar}] {done}/{total} ({pct:.0f}%) {current}"
        self.notifier.send("进度报告", msg)

    def summary(self, report: dict):
        msg = (
            f"刷课完成报告\n"
            f"总课程: {report.get('total', 0)}\n"
            f"已完成: {report.get('completed', 0)}\n"
            f"成功率: {report.get('success_rate', 0):.0f}%\n"
            f"用时: {report.get('duration', '')}"
        )
        self.notifier.send("刷课完成", msg)
