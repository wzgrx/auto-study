"""
09 — 万能登录层
支持任何网站的自动登录：Cookie 恢复 → 填表 → 验证码重试
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
              selectors: dict = None, plugin=None) -> bool:
        domain = url.split("//")[-1].split("/")[0]

        # 1. 尝试 Cookie 恢复
        if self.persist.restore(tab, domain):
            time.sleep(2)
            if self._check_logged_in(tab):
                logger.info(f"✅ {domain}: Cookie 登录成功")
                return True

        # 2. 导航到登录页
        self.brain.tm.navigate(tab, url)
        time.sleep(3)

        # 3. 填表（最多尝试 3 次验证码）
        for attempt in range(3):
            self._fill_form(tab, username, password, selectors, plugin)
            time.sleep(3)

            if self._check_logged_in(tab):
                self.persist.save(tab, domain)
                logger.info(f"✅ 登录成功: {username}")
                return True

            # 验证码错误 → 刷新验证码重试
            if attempt < 2:
                logger.warning(f"登录失败，重试验证码 ({attempt + 1}/3)")
                self._refresh_captcha(tab, selectors)

        raise LoginError(f"登录失败 ({username})")

    def _fill_form(self, tab, username, password, sel, plugin=None):
        """填表"""
        user_sel = (sel or {}).get("username", "input.el-input__inner")
        pass_sel = (sel or {}).get("password", "input[type='password']")
        js_user = (plugin.login_js if plugin and hasattr(plugin, 'login_js')
                   else {}).get("username", "")

        self.brain.input_text(tab, user_sel, username, js_selector=js_user)
        self.brain.input_text(tab, pass_sel, password)

        # 验证码
        cap_sel = (sel or {}).get("captcha_input", "")
        if cap_sel:
            code = self.captcha.solve(tab)
            if code:
                self.brain.input_text(tab, cap_sel, code)

        # 点击登录
        submit_sel = (sel or {}).get("submit", "")
        submit_text = (plugin.login_js if plugin and hasattr(plugin, 'login_js')
                       else {}).get("submit_text", "")
        self.brain.click(tab, selector=submit_sel, js_text=submit_text)

    def _refresh_captcha(self, tab, sel):
        """刷新验证码"""
        if sel and "captcha_img" in sel:
            try:
                tab.ele(sel["captcha_img"], timeout=3).click()
                time.sleep(1)
            except Exception:
                pass

    @staticmethod
    def _check_logged_in(tab) -> bool:
        url = (tab.url or "").lower()
        text = (tab.ele("tag:body").text or "").lower()
        if "login" not in url and "vuelogin" not in url:
            return True
        login_keywords = ["退出", "logout", "个人中心", "dashboard"]
        if any(kw in text for kw in login_keywords):
            return True
        return False
