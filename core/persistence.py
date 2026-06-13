"""
07 — 持久化层
Cookie 会话管理
"""
from __future__ import annotations
import logging
from core.config import Config

logger = logging.getLogger("persistence")


class SessionManager:
    """登录会话管理"""

    def save(self, tab, domain: str):
        cookies = tab.run_js("return document.cookie")
        path = Config.COOKIE_DIR / f"{domain}.txt"
        path.write_text(cookies)
        logger.info(f"Cookie 已保存: {domain}")

    def restore(self, tab, domain: str) -> bool:
        path = Config.COOKIE_DIR / f"{domain}.txt"
        if not path.exists():
            return False
        cookies = path.read_text()
        tab.run_js(f"document.cookie='{cookies}'")
        tab.get(tab.url)
        logger.info(f"Cookie 已恢复: {domain}")
        return True

    def clear(self, domain: str):
        path = Config.COOKIE_DIR / f"{domain}.txt"
        if path.exists():
            path.unlink()
