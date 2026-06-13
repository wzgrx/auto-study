"""
17 — 报告层
进度报告 + 完成总结
"""
from __future__ import annotations
import logging
from core.notifier import Notifier

logger = logging.getLogger("reporter")


class Reporter:
    """报告器"""

    def __init__(self):
        self.note = Notifier()

    def progress(self, done: int, total: int, current: str = ""):
        pct = done / total * 100 if total else 0
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        self.note.send("进度", f"[{bar}] {done}/{total} ({pct:.0f}%) {current}")

    def summary(self, stats: dict, duration: str = ""):
        self.note.send("刷课完成",
            f"总课程: {stats.get('total',0)}\n已完成: {stats.get('completed',0)}\n"
            f"成功率: {stats.get('rate',0):.0f}%\n用时: {duration}")
