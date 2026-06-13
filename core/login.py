"""
09 — 万能登录层
支持任何网站的自动登录（已知选择器 / AI 分析）
"""
from __future__ import annotations
import time
import logging
from core.exceptions import LoginError, retry
from core.captcha import CaptchaSolver

logger = logging.getLogger("login")


class UniversalLogin:
    """万能登录器"""

    def __init__(self, brain, persistence):
        self.brain = brain
        self.persist = persistence
        self.captcha = CaptchaSolver(brain)

    @retry(max_attempts=3, delay=30)
    def login(self, tab, url: str, username: str, password: str,
              selectors: dict = None) -> bool:
        # 尝试恢复会话
        domain = url.split("//")[-1].split("/")[0]
        if self.persist.restore(tab, domain):
            if self._check_logged_in(tab):
                logger.info(f"{domain}: Cookie 登录成功")
                return True

        self.brain.tm.navigate(tab, url)

        if selectors:
            self._fill_form(tab, username, password, selectors)
        else:
            self._fill_with_vision(tab, username, password)

        time.sleep(3)
        if self._check_logged_in(tab):
            self.persist.save(tab, domain)
            logger.info(f"登录成功: {username}")
            return True

        raise LoginError(f"登录失败: {username}")

    def _fill_form(self, tab, username, password, sel):
        if "username" in sel:
            self.brain.input_text(tab, sel["username"], username)
        if "password" in sel:
            self.brain.input_text(tab, sel["password"], password)
        if "captcha_input" in sel:
            code = self.captcha.solve(tab)
            self.brain.input_text(tab, sel["captcha_input"], code)
        self.brain.click(tab, sel.get("submit", "button[type='submit']"))

    def _fill_with_vision(self, tab, username, password):
        analysis = self.brain.analyze_screenshot(
            tab, "描述登录表单：用户名框、密码框、验证码、登录按钮位置？")
        logger.info(f"AI 分析页面: {analysis[:200]}")
        # 简化的默认填充
        self.brain.input_text(tab, "input[type='text']", username)
        self.brain.input_text(tab, "input[type='password']", password)
        self.brain.click(tab, "button[type='submit']")

    @staticmethod
    def _check_logged_in(tab) -> bool:
        text = (tab.ele("tag:body").text or "").lower()
        return not any(kw in text for kw in ["登录", "login", "密码错误", "请输入密码"])
