"""
15 — 站点插件体系
标准化插件接口 + 注册中心 + 双模选择器
"""
from __future__ import annotations
from abc import ABC
from dataclasses import dataclass, field


class SitePlugin(ABC):
    """站点插件基类

    每个站点插件包含:
    - login_selectors: DrissionPage ele() 用
    - login_js: querySelector/querySelectorAll 用（降级时使用）
    """
    name: str = ""
    domains: list[str] = field(default_factory=list)
    login_url: str = ""
    login_selectors: dict = field(default_factory=dict)
    login_js: dict = field(default_factory=dict)


class PluginRegistry:
    """插件注册中心"""
    _plugins: dict[str, SitePlugin] = {}

    @classmethod
    def register(cls, plugin: SitePlugin):
        for d in plugin.domains:
            cls._plugins[d] = plugin

    @classmethod
    def get(cls, url: str) -> SitePlugin | None:
        """根据 URL 匹配插件"""
        for d, p in cls._plugins.items():
            if d in url:
                return p
        return None


# ═══════════════════════════════════════════
# Chinahrt 插件
# ═══════════════════════════════════════════

class ChinahrtPlugin(SitePlugin):
    name = "chinahrt"
    domains = ["gp.chinahrt.com", "chinahrt.com"]
    login_url = "https://gp.chinahrt.com/index.html#/commonLogin"

    login_selectors = {
        "username": ("input.el-input__inner", 1),  # (selector, index)
        "password": ("input.el-input__inner", 2),
        "captcha_input": ("input.el-input__inner", 3),
        "captcha_img": "img[src*='kaptcha']",
        "submit": ("button", 1),
    }
    login_js = {
        "username": "input.el-input__inner",
        "submit_text": "登录",
    }


# ═══════════════════════════════════════════
# 华医网插件
# ═══════════════════════════════════════════

class HuayiPlugin(SitePlugin):
    name = "huayiwang"
    domains = ["91huayi.com", "cme", "yxlearning.com"]
    login_url = "https://www.91huayi.com/"
    login_selectors = {}
    login_js = {}


# 注册
PluginRegistry.register(ChinahrtPlugin())
PluginRegistry.register(HuayiPlugin())
