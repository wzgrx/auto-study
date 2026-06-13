"""
14 — 健康监控
长时间运行检测：心跳、浏览器存活、自动恢复
"""
from __future__ import annotations
import time
import logging

logger = logging.getLogger("health")


class HealthMonitor:
    """健康监控器"""

    def __init__(self, stall_sec: int = 300):
        self._last = time.time()
        self._stall_sec = stall_sec

    def heartbeat(self):
        self._last = time.time()

    @property
    def alive(self) -> bool:
        return time.time() - self._last < self._stall_sec

    def check_browser(self, tab_manager) -> bool:
        try:
            tab_manager.get()
            return True
        except Exception as e:
            logger.error(f"浏览器异常: {e}")
            return False
