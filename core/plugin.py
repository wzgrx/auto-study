"""
15 — 站点插件体系
标准化插件接口 + 注册中心
"""
from __future__ import annotations
from abc import ABC
from dataclasses import dataclass, field


class SitePlugin(ABC):
    """站点插件基类"""
    name: str = ""
    domains: list[str] = field(default_factory=list)
    login_url: str = ""
    login_selectors: dict = field(default_factory=dict)


class PluginRegistry:
    """插件注册中心"""
    _plugins: dict[str, SitePlugin] = {}

    @classmethod
    def register(cls, plugin: SitePlugin):
        for d in plugin.domains:
            cls._plugins[d] = plugin

    @classmethod
    def get(cls, url: str) -> SitePlugin | None:
        for d, p in cls._plugins.items():
            if d in url:
                return p
        return None


# ── 内置插件 ──

class ChinahrtPlugin(SitePlugin):
    name = "chinahrt"
    domains = ["gp.chinahrt.com", "chinahrt.com"]
    login_url = "https://gp.chinahrt.com/index.html#/commonLogin"
    login_selectors = {
        "username": "input[type='text']",
        "password": "input[type='password']",
        "submit": "button[type='submit']",
    }


class HuayiPlugin(SitePlugin):
    name = "huayiwang"
    domains = ["91huayi.com", "cme", "yxlearning.com"]
    login_url = "https://www.91huayi.com/"
    login_selectors = {}


# 注册
PluginRegistry.register(ChinahrtPlugin())
PluginRegistry.register(HuayiPlugin())
