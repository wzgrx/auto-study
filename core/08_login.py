"""
08 - 万能登录层
支持任何网站的自动登录（已知选择器 / AI 分析）
"""
from __future__ import annotations
import logging
from core.config import Config
from core.brain import BrowserBrain
from core.captcha import CaptchaSolver
from core.exceptions import LoginError, retry

logger = logging.getLogger("login")


class UniversalLogin:
    """万能登录器"""

    def __init__(self, brain: BrowserBrain):
        self.brain = brain
        self.captcha = CaptchaSolver()

    @retry(max_attempts=3, delay=30)
    def login(self, url: str, username: str, password: str, selectors: dict = None) -> bool:
        """登录任意网站"""
        tab = self.brain.get_tab(0)
        self.brain.navigate(tab, url)

        if selectors:
            return self._login_with_selectors(tab, username, password, selectors)
        return self._login_with_vision(tab, username, password)

    def _login_with_selectors(self, tab, username, password, sel) -> bool:
        if "username" in sel:
            self.brain.input_text(tab, sel["username"], username)
        if "password" in sel:
            self.brain.input_text(tab, sel["password"], password)
        if "captcha_input" in sel:
            code = self.captcha.solve(tab)
            self.brain.input_text(tab, sel["captcha_input"], code)
        self.brain.click(tab, sel.get("submit", "button[type='submit']"))
        return self._verify(tab)

    def _login_with_vision(self, tab, username, password) -> bool:
        analysis = self.brain.analyze_screenshot(
            tab, "描述登录表单：用户名框、密码框、验证码、登录按钮的位置？")
        logger.info(f"页面分析: {analysis[:200]}")
        return False

    def _verify(self, tab) -> bool:
        text = self.brain.read_text(tab)
        return not any(kw in text for kw in ["登录", "login", "密码错误"])
