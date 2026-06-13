"""
05 — 基础能力层（核心大脑）
封装 DrissionPage 操作 + Gemma 4 视觉 + JS 安全执行
"""
from __future__ import annotations
import time
import random
import base64
import json
import logging
import httpx
from core.config import Config

logger = logging.getLogger("brain")


class BrowserBrain:
    """浏览器大脑"""

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

    # ── JS 安全执行（修复：避免引号嵌套）──

    def js_call(self, tab, js_template: str, **kwargs):
        """安全执行 JS，参数通过 JSON 序列化避免引号问题

        用法:
            brain.js_call(tab, "el.value = {text}", text="hello")
            # → el.value = "hello"  (自动处理引号)
        """
        # 把参数用 JSON 序列化，确保引号安全
        safe_kwargs = {k: json.dumps(v, ensure_ascii=False) for k, v in kwargs.items()}
        js_code = js_template.format(**safe_kwargs)
        return tab.run_js(js_code)

    # ── 页面操作 ──

    def input_text(self, tab, selector, text: str, js_selector: str = ""):
        """输入文字 — DrissionPage 优先，失败降级到 JS

        Args:
            selector: DrissionPage 选择器，可以是字符串或 (字符串, index) 元组
            text: 要输入的文字
            js_selector: JS querySelector 选择器 (降级时用)
        """
        index = 1
        if isinstance(selector, (list, tuple)):
            selector, index = selector

        try:
            el = tab.ele(selector, index=index, timeout=5)
            el.clear()
            el.input(text)
        except Exception:
            qs = js_selector or selector
            safe_text = json.dumps(text, ensure_ascii=False)
            tab.run_js(f"""
                var els = document.querySelectorAll({json.dumps(qs)});
                var el = els[{index - 1}] || els[0];
                if (el) {{
                    el.value = {safe_text};
                    el.dispatchEvent(new Event('input', {{bubbles: true}}));
                    el.dispatchEvent(new Event('change', {{bubbles: true}}));
                }}
            """)
        time.sleep(random.uniform(0.3, 1.0))

    def click(self, tab, selector: str = "", js_text: str = "", timeout=10):
        """点击 — DrissionPage 优先，失败降级到 JS

        Args:
            selector: DrissionPage 选择器，可以是字符串或 (字符串, index) 元组
            js_text: JS 中按文本匹配点击时用的文字
        """
        index = 1
        if isinstance(selector, (list, tuple)):
            selector, index = selector

        if selector:
            try:
                el = tab.ele(selector, index=index, timeout=timeout)
                el.click()
            except Exception:
                if js_text:
                    safe_text = json.dumps(js_text, ensure_ascii=False)
                    tab.run_js(f"""
                        var btns = document.querySelectorAll('button,a,.el-button');
                        for(var b of btns){{
                            if(b.textContent.trim() === {safe_text})
                            {{ b.click(); break; }}
                        }}
                    """)
        time.sleep(random.uniform(*Config.HUMAN_DELAY_SEC))

    def execute_js(self, tab, js: str):
        return tab.run_js(js)

    def wait(self, sec: float = 2):
        time.sleep(sec)
