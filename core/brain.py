"""
05 — 基础能力层（核心大脑）
封装 DrissionPage 基本操作 + Gemma 4 视觉分析
"""
from __future__ import annotations
import time
import random
import base64
import logging
import httpx
from core.config import Config

logger = logging.getLogger("brain")


class BrowserBrain:
    """浏览器大脑 — 所有业务模块通过此类操作浏览器"""

    def __init__(self, tab_manager):
        self.tm = tab_manager

    # ── 阅读页面 ──

    def read_text(self, tab) -> str:
        return tab.ele("tag:body").text

    def read_title(self, tab) -> str:
        return tab.title

    def read_url(self, tab) -> str:
        return tab.url

    def read_hash(self, tab) -> str:
        return tab.run_js("return location.hash")

    # ── 视觉分析 ──

    def analyze_screenshot(self, tab, question: str) -> str:
        """截图 → Gemma 4 分析 → 返回结果"""
        try:
            path = tab.get_screenshot()
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            resp = httpx.post(
                f"{Config.GEMMA_URL}/chat/completions",
                json={
                    "model": "gemma-4-12b",
                    "messages": [{"role": "user", "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                        {"type": "text", "text": question}]}],
                    "max_tokens": 2048,
                },
                timeout=30,
            )
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"Gemma 分析失败: {e}")
            return ""

    # ── 页面操作 ──

    def click(self, tab, selector_or_el, timeout=10):
        if isinstance(selector_or_el, str):
            el = tab.ele(selector_or_el, timeout=timeout)
        else:
            el = selector_or_el
        el.click()
        time.sleep(random.uniform(*Config.HUMAN_DELAY_SEC))

    def input_text(self, tab, selector, text: str):
        el = tab.ele(selector)
        el.clear()
        el.input(text)
        time.sleep(random.uniform(0.3, 1.0))

    def execute_js(self, tab, js: str):
        return tab.run_js(js)

    def wait(self, sec: float = 2):
        time.sleep(sec)
