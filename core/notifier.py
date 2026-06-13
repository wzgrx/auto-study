"""
13 — 通知模块
多通道：控制台 / 飞书 / 微信
"""
from __future__ import annotations
import logging
from core.config import Config

logger = logging.getLogger("notifier")


class Notifier:
    """多通道通知"""

    def send(self, title: str, message: str):
        logger.info(f"[{title}] {message}")
        if Config.FEISHU_WEBHOOK:
            self._feishu(title, message)

    def _feishu(self, title: str, message: str):
        try:
            import requests
            requests.post(Config.FEISHU_WEBHOOK, json={
                "msg_type": "text",
                "content": {"text": f"{title}\n{message}"},
            }, timeout=5)
        except Exception as e:
            logger.warning(f"飞书推送失败: {e}")
