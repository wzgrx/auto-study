"""
08 — 验证码处理
多策略识别：ddddocr / Gemma 4 / 人工
"""
from __future__ import annotations
import logging
import time
from core.exceptions import CaptchaError

logger = logging.getLogger("captcha")


class CaptchaSolver:
    """验证码识别器"""

    def solve(self, tab) -> str:
        # 策略1: ddddocr
        result = self._ocr(tab)
        if result:
            return result
        # 策略2: Gemma
        result = self._vision(tab)
        if result:
            return result
        # 策略3: 人工
        return self._manual(tab)

    def _ocr(self, tab) -> str:
        try:
            import ddddocr
            img = tab.ele("tag:img", timeout=3)
            if not img:
                return ""
            src = (img.attr("src") or "").lower()
            if "captcha" not in src and "verify" not in src and "code" not in src:
                return ""
            ocr = ddddocr.DdddOcr(show_ad=False)
            return ocr.classification(img.src) or ""
        except Exception:
            return ""

    def _vision(self, tab) -> str:
        try:
            from core.brain import BrowserBrain
            brain = BrowserBrain(None)
            return brain.analyze_screenshot(tab, "识别验证码，只输出结果")
        except Exception:
            return ""

    def _manual(self, tab) -> str:
        path = tab.get_screenshot()
        logger.warning(f"验证码识别失败，截图已保存: {path}")
        raise CaptchaError(f"需要人工输入验证码，查看截图: {path}")
