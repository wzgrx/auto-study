"""
02 — 标签页管理器（重写）
基于 Pydoll singleton + BrowserStack 智能匹配

核心原则：
1. 复用已有标签页，绝不无故新建
2. get() 按 URL/title 智能匹配，match 不到才新建
3. 每次只创建刚够用的标签页，用完释放
4. 显式生命周期管理
"""
from __future__ import annotations
import time
import logging
from typing import Any
from DrissionPage import Chromium
from core.config import Config

logger = logging.getLogger("tab_manager")


class TabManager:
    """标签页管理器

    用法:
        tm = TabManager()
        tab = tm.get("https://gp.chinahrt.com")    # 按 URL 匹配
        tab = tm.create()                           # 明确说要新建
        tm.close_all()                              # 用完清理
    """

    def __init__(self):
        self.browser: Chromium = Chromium(Config.CDP_PORT)
        # 缓存所有标签页: {tab_id: tab对象}
        # 不预设"池大小"，按需使用
        self._tabs: dict[str, Any] = {}
        self._initial_tab = None
        self._refresh_cache()
        logger.info(f"浏览器已连接: Edge:{Config.CDP_PORT} ({len(self._tabs)} 个标签页)")

    # ═══════════════════════════════════════════
    # 核心 API：获取标签页
    # ═══════════════════════════════════════════

    def get(self, url: str = "", title: str = ""):
        """获取标签页 — 优先匹配已有，匹配不到才新建（Pydoll singleton 模式）

        匹配策略（BrowserStack smart tab handling）:
          1. URL 精确匹配
          2. URL 关键词匹配
          3. title 匹配
          4. 返回第一个空白标签页
          5. 新建
        """
        self._refresh_cache()
        if not self._tabs:
            return self.create()

        # 策略1: URL 精确匹配
        if url:
            for t in self._tabs.values():
                if t.url and url == t.url:
                    return t

        # 策略2: URL 关键词匹配
        if url:
            for t in self._tabs.values():
                if t.url and url in t.url:
                    return t

        # 策略3: title 匹配
        if title:
            for t in self._tabs.values():
                if t.title and title in t.title:
                    return t

        # 策略4: 空白标签页
        for t in self._tabs.values():
            if not t.url or t.url in ("about:blank", "", "edge://newtab/"):
                return t

        # 策略5: 第一个可用标签页
        first = next(iter(self._tabs.values()))
        return first

    def create(self):
        """明确要求新建标签页"""
        tab = self.browser.new_tab()
        self._tabs[tab.tab_id] = tab
        logger.debug(f"新建标签页: {tab.tab_id[:12]}")
        return tab

    # ═══════════════════════════════════════════
    # 导航
    # ═══════════════════════════════════════════

    @staticmethod
    def navigate(tab, url: str, timeout: int = 15):
        """导航并等待"""
        tab.get(url)
        # DrissionPage 自带超时，不需要额外控制
        time.sleep(3)

    @staticmethod
    def navigate_hash(tab, hash_str: str):
        """SPA hash 导航"""
        if not hash_str.startswith("#"):
            hash_str = "#" + hash_str
        tab.run_js(f"location.hash='{hash_str}'")
        time.sleep(3)

    # ═══════════════════════════════════════════
    # 缓存刷新
    # ═══════════════════════════════════════════

    def _refresh_cache(self):
        """刷新标签页缓存"""
        try:
            all_tabs = self.browser.get_tabs()
            current_ids = {t.tab_id for t in all_tabs}
            for tid in list(self._tabs.keys()):
                if tid not in current_ids:
                    del self._tabs[tid]
            for t in all_tabs:
                if t.tab_id not in self._tabs:
                    self._tabs[t.tab_id] = t
                    if self._initial_tab is None:
                        self._initial_tab = t
        except Exception as e:
            logger.warning(f"刷新标签页缓存失败: {e}")

    # ═══════════════════════════════════════════
    # 清理
    # ═══════════════════════════════════════════

    def close_all(self):
        """关闭所有标签页"""
        for tab in self._tabs.values():
            try:
                tab.close()
            except Exception:
                pass
        self._tabs.clear()
        self._initial_tab = None

    def close_extra(self, keep_ids: set = None):
        """关闭除了 keep_ids 之外的标签页"""
        self._refresh_cache()
        for tid, tab in list(self._tabs.items()):
            if keep_ids and tid in keep_ids:
                continue
            try:
                tab.close()
            except Exception:
                pass
            del self._tabs[tid]

    # ═══════════════════════════════════════════
    # 信息
    # ═══════════════════════════════════════════

    def list_tabs(self) -> list[dict]:
        self._refresh_cache()
        result = []
        for tab in self._tabs.values():
            result.append({
                "tab_id": tab.tab_id[:16] if tab.tab_id else "",
                "title": (tab.title or "")[:50],
                "url": (tab.url or "")[:80],
            })
        return result

    @property
    def count(self) -> int:
        self._refresh_cache()
        return len(self._tabs)
