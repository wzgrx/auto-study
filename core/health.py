"""
13 - 健康监控
长时间运行时的健康检测、心跳、自动恢复
"""
from __future__ import annotations
import time
import logging
from core.config import Config

logger = logging.getLogger("health")


class HealthMonitor:
    """健康监控器"""

    def __init__(self):
        self._last_heartbeat = time.time()
        self._stall_threshold = 300

    def heartbeat(self):
        self._last_heartbeat = time.time()

    def is_alive(self) -> bool:
        return time.time() - self._last_heartbeat < self._stall_threshold

    def check_browser(self, brain) -> bool:
        try:
            brain.get_tab(0)
            return True
        except Exception:
            logger.error("浏览器连接异常")
            return False
