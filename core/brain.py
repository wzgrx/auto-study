"""
04 - 基础能力层（核心大脑）
封装 DrissionPage + DeepSeek + Gemma 4 的所有基础操作
"""
from __future__ import annotations
import time
import random
import logging
from DrissionPage import Chromium
from core.config import Config

logger = logging.getLogger("brain")


class BrowserBrain:
    """浏览器大脑 — 所有上层模块只通过这个类操作浏览器"""

    def __init__(self):
        self.browser = Chromium(addr=Config.CDP_PORT)
        logger.info(f"浏览器已连接: Edge:{Config.CDP_PORT}")

    # ── 标签页管理 ──

    def get_tab(self, index: int = 0):
        """获取指定标签页"""
        return self.browser.get_tab(index)

    def get_all_tabs(self):
        return [self.browser.get_tab(i) for i in range(3)]

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
        """截图 → Gemma 4 分析 → 返回文字理解"""
        import base64
        import httpx
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

    # ── 页面操作 ──

    def click(self, tab, selector_or_el, timeout=10):
        if isinstance(selector_or_el, str):
            el = tab.ele(selector_or_el, timeout=timeout)
        else:
            el = selector_or_el
        el.click()
        time.sleep(random.uniform(*Config.HUMAN_DELAY))

    def input_text(self, tab, selector, text: str):
        el = tab.ele(selector)
        el.clear()
        el.input(text)
        time.sleep(random.uniform(0.3, 1.0))

    def navigate(self, tab, url: str):
        tab.get(url)
        time.sleep(2)

    def navigate_hash(self, tab, hash_str: str):
        if not hash_str.startswith("#"):
            hash_str = "#" + hash_str
        tab.run_js(f"location.hash='{hash_str}'")
        time.sleep(3)

    def execute_js(self, tab, js: str):
        return tab.run_js(js)
