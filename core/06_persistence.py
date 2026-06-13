"""
06 - 持久化层
Cookie 会话保存恢复、进度持久化
"""
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
from core.config import Config

logger = __import__("logging").getLogger("persistence")


class SessionManager:
    """登录会话管理"""

    def __init__(self):
        self.cookie_dir = Config.COOKIE_DIR
        self.cookie_dir.mkdir(parents=True, exist_ok=True)

    def save(self, domain: str, tab):
        cookies = tab.run_js("return document.cookie")
        (self.cookie_dir / f"{domain}.txt").write_text(cookies)
        logger.info(f"Cookie 已保存: {domain}")

    def restore(self, domain: str, tab) -> bool:
        path = self.cookie_dir / f"{domain}.txt"
        if not path.exists():
            return False
        cookies = path.read_text()
        tab.run_js(f"document.cookie='{cookies}'")
        logger.info(f"Cookie 已恢复: {domain}")
        return True
