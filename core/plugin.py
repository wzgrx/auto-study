"""
14 - 站点插件体系
标准化插件接口 + 注册中心
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class SitePlugin(ABC):
    """站点插件基类"""
    name: str = ""
    domains: list[str] = field(default_factory=list)
    login_selectors: dict = field(default_factory=dict)
    course_selectors: dict = field(default_factory=dict)
    video_selectors: dict = field(default_factory=dict)


class PluginRegistry:
    """插件注册中心"""
    _plugins: dict[str, SitePlugin] = {}

    @classmethod
    def register(cls, plugin: SitePlugin):
        for domain in plugin.domains:
            cls._plugins[domain] = plugin

    @classmethod
    def get(cls, domain: str) -> SitePlugin | None:
        for d, p in cls._plugins.items():
            if d in domain:
                return p
        return None

    @classmethod
    def detect(cls, url: str) -> SitePlugin | None:
        for domain, plugin in cls._plugins.items():
            if domain in url:
                return plugin
        return None
