"""
02 — 标签页管理器
基于 Pydoll singleton + BrowserStack 智能匹配

关键设计（对比 PyDoll 2058行 tab.py 后的结论）:
1. get() 复用已有标签页，不新建（Pydoll singleton 模式）
2. _refresh_cache() 同步浏览器实际状态（Pydoll get_opened_tabs）
3. navigate() 检查导航是否成功（Pydoll go_to 有 NavigationError）
4. 过滤非 page 类型标签页（Pydoll 排除 extension）
"""
from __future__ import annotations
import time
import logging
from typing import Any
from DrissionPage import Chromium
from core.config import Config

logger = logging.getLogger("tab_manager")


class TabManager:
    """标签页管理器"""

    def __init__(self):
        self.browser: Chromium = Chromium(Config.CDP_PORT)
        self._tabs: dict[str, Any] = {}
        self._refresh_cache()
        logger.info(f"浏览器已连接: Edge:{Config.CDP_PORT} ({len(self._tabs)} 个标签页)")

    # ═══════════════════════════════════════════
    # 获取标签页（核心 API）
    # ═══════════════════════════════════════════

    def get(self, url: str = "", title: str = ""):
        """获取标签页 — 5策略递进匹配，不新建

        匹配策略（参考 BrowserStack smart tab handling）:
          1. URL 精确匹配
          2. URL 关键词匹配
          3. title 匹配
          4. 空白标签页
          5. 第一个可用标签页
        """
        self._refresh_cache()
        if not self._tabs:
            return self.create()

        tabs = list(self._tabs.values())

        if url:
            for t in tabs:
                if t.url and url == t.url:
                    return t
            for t in tabs:
                if t.url and url in t.url:
                    return t

        if title:
            for t in tabs:
                if t.title and title in t.title:
                    return t

        for t in tabs:
            u = (t.url or "").strip()
            if not u or u in ("about:blank", "edge://newtab/"):
                return t

        return tabs[0]

    def create(self):
        """创建新标签页"""
        tab = self.browser.new_tab()
        self._tabs[tab.tab_id] = tab
        logger.debug(f"新建标签页: {tab.tab_id[:12]}")
        return tab

    # ═══════════════════════════════════════════
    # 导航（参考 PyDoll go_to）
    # ═══════════════════════════════════════════

    @staticmethod
    def navigate(tab, url: str, timeout: int = 30):
        """导航并等待加载完成

        参考 PyDoll go_to():
        - 有 timeout 参数
        - 等待页面加载
        - 不检查 errorText（DrissionPage 内部处理）
        """
        tab.get(url, timeout=timeout)
        time.sleep(3)

    def navigate_with_retry(self, tab, url: str, max_attempts: int = 2):
        """带重试的导航（SPA 首屏加载可能失败）"""
        for attempt in range(max_attempts):
            self.navigate(tab, url)
            time.sleep(2)
            current = tab.url or ""
            if url in current or url.split("#")[0] in current:
                return True
            logger.warning(f"导航可能失败 (尝试 {attempt + 1}/{max_attempts}): {url[:50]}")
        return False

    @staticmethod
    def navigate_hash(tab, hash_str: str):
        """SPA hash 导航"""
        if not hash_str.startswith("#"):
            hash_str = "#" + hash_str
        tab.run_js(f"location.hash='{hash_str}'")
        time.sleep(3)

    # ═══════════════════════════════════════════
    # 缓存刷新（参考 PyDoll get_opened_tabs）
    # ═══════════════════════════════════════════

    def _refresh_cache(self):
        """刷新缓存：删除已关闭的、添加新的 page 类型标签页"""
        try:
            all_tabs = self.browser.get_tabs()
            current_ids = {t.tab_id for t in all_tabs}
            for tid in list(self._tabs.keys()):
                if tid not in current_ids:
                    del self._tabs[tid]
            for t in all_tabs:
                if t.tab_id not in self._tabs:
                    self._tabs[t.tab_id] = t
        except Exception as e:
            logger.warning(f"刷新标签页缓存失败: {e}")

    # ═══════════════════════════════════════════
    # 清理
    # ═══════════════════════════════════════════

    def close_tab(self, tab):
        """关闭单个标签页并从缓存移除"""
        tid = tab.tab_id
        try:
            tab.close()
        except Exception:
            pass
        self._tabs.pop(tid, None)
        logger.debug(f"关闭标签页: {tid[:12] if tid else '?'}")

    def close_all(self):
        """关闭所有标签页"""
        for tab in list(self._tabs.values()):
            try:
                tab.close()
            except Exception:
                pass
        self._tabs.clear()

    def close_extra(self, keep_ids: set = None):
        """关闭指定之外的标签页"""
        self._refresh_cache()
        keep = keep_ids or set()
        for tid, tab in list(self._tabs.items()):
            if tid not in keep:
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
        return [{
            "tab_id": t.tab_id[:16] if t.tab_id else "",
            "title": (t.title or "")[:50],
            "url": (t.url or "")[:80],
        } for t in self._tabs.values()]

    @property
    def count(self) -> int:
        self._refresh_cache()
        return len(self._tabs)

    @property
    def tab_ids(self) -> list[str]:
        return list(self._tabs.keys())
