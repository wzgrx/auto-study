"""
07 - 验证码处理
多策略识别：ddddocr / Gemma 4 / 2Captcha / 人工
"""
from __future__ import annotations
import logging

logger = logging.getLogger("captcha")


class CaptchaSolver:
    """验证码识别器"""

    def solve(self, tab) -> str:
        """自动识别验证码，返回识别结果"""
        # 策略1: ddddocr
        result = self._ocr_ddddocr(tab)
        if result:
            return result
        # 策略2: Gemma 看图
        result = self._vision_gemma(tab)
        if result:
            return result
        # 策略3: 人工
        return self._manual_input(tab)

    def _ocr_ddddocr(self, tab) -> str:
        """ddddocr 识别数字字母验证码"""
        try:
            import ddddocr
            img_el = tab.ele("tag:img", timeout=3)
            if img_el and ("captcha" in (img_el.attr("src") or "").lower()
                           or "verify" in (img_el.attr("src") or "").lower()):
                ocr = ddddocr.DdddOcr(show_ad=False)
                img_bytes = img_el.src
                result = ocr.classification(img_bytes)
                if result and len(result) >= 3:
                    return result
        except Exception:
            pass
        return ""

    def _vision_gemma(self, tab) -> str:
        """Gemma 4 看图识别复杂验证码"""
        from core.brain import BrowserBrain
        brain = BrowserBrain()
        return brain.analyze_screenshot(tab, "请识别验证码中的文字，只输出识别结果")

    def _manual_input(self, tab) -> str:
        """人工输入验证码"""
        import os
        logger.warning("验证码识别失败，需要人工介入")
        return input("请查看截图并输入验证码: ")
