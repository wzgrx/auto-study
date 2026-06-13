"""
12 - 通知模块
多通道通知：飞书 / 控制台 / 微信 / 邮件
"""
from __future__ import annotations
import logging
from core.config import Config

logger = logging.getLogger("notifier")


class Notifier:
    """多通道通知"""

    def send(self, title: str, message: str):
        self.console(title, message)
        if Config.FEISHU_WEBHOOK:
            self.feishu(title, message)

    def console(self, title: str, message: str):
        logger.info(f"[{title}] {message}")

    def feishu(self, title: str, message: str):
        import requests
        try:
            requests.post(Config.FEISHU_WEBHOOK, json={
                "msg_type": "text",
                "content": {"text": f"{title}\n{message}"},
            }, timeout=5)
        except Exception as e:
            logger.warning(f"飞书推送失败: {e}")
