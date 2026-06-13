"""
02 — 智能标签页管理器
动态标签页池：自动识别、按需创建、智能复用、自动清理

替代旧的"3固定标签页"模式，支持：
- 按需创建标签页
- 按URL/标题自动识别已有标签页
- 智能复用（找到匹配的就不新建）
- 标签页池大小动态调节
- 自动清理无用标签页
"""
from __future__ import annotations
import time
import logging
from typing import Any
from DrissionPage import Chromium
from core.config import Config

logger = logging.getLogger("tab_manager")


class TabManager:
    """智能标签页管理器

    用法:
        tm = TabManager()
        tab = tm.get("课程列表")       # 按用途获取
        tab = tm.get(url="...")        # 按URL匹配
        tab = tm.create()              # 创建新标签页
        tm.close_unused()              # 自动清理
    """

    def __init__(self, min_pool: int = 2):
        self.browser: Chromium = Chromium(Config.CDP_PORT)
        self._pool: dict[str, Any] = {}  # {tag: tab对象}
        self.discover()                   # 发现已有标签页
        self.ensure_min_pool(min_pool)
        logger.info(f"浏览器已连接: Edge:{Config.CDP_PORT}")

    # ═══════════════════════════════════════════
    # 标签页获取（核心API）
    # ═══════════════════════════════════════════

    def get(self, tag: str = "", url: str = "", title: str = ""):
        """获取标签页 — 智能匹配，找不到就新建

        匹配优先级:
          1. 按 tag 精确匹配（手动标记的标签页）
          2. 按 URL 关键词匹配
          3. 按 title 关键词匹配
          4. 创建新的标签页
        """
        if tag and tag in self._pool:
            return self._pool[tag]
        if url:
            for t in self._pool.values():
                if url in (t.url or ""):
                    return t
        if title:
            for t in self._pool.values():
                if title in (t.title or ""):
                    return t
        return self.create(tag)

    def create(self, tag: str = ""):
        """创建新标签页并加入池"""
        tab = self.browser.new_tab()
        if tag:
            self._pool[tag] = tab
        logger.debug(f"新建标签页: tag={tag or '未标记'} tab_id={tab.tab_id[:12]}")
        return tab

    def tag(self, tab, tag: str):
        """给标签页打标记"""
        self._pool[tag] = tab

    # ═══════════════════════════════════════════
    # 标签页发现
    # ═══════════════════════════════════════════

    def discover(self):
        """发现浏览器中已有标签页，按特征自动归类"""
        discovered = []
        for tab in self.browser.get_tabs():
            if not tab.tab_id:
                continue
            url = tab.url or ""
            if "chinahrt.com" in url:
                if "v_selected_course" in url:
                    self._pool.setdefault("课程列表", tab)
                elif "v_courseDetails" in url:
                    self._pool.setdefault("课程详情", tab)
                elif "v_video" in url:
                    self._pool.setdefault("视频播放", tab)
                elif "commonLogin" in url or "vuelogin" in url:
                    self._pool.setdefault("登录", tab)
                discovered.append(tab)
            elif "91huayi.com" in url or "cme" in url:
                if "course_ware" in url:
                    self._pool.setdefault("视频播放", tab)
                elif "course.aspx" in url:
                    self._pool.setdefault("课程列表", tab)
                elif "exam" in url:
                    self._pool.setdefault("考试", tab)
                discovered.append(tab)
            elif url and "about:blank" not in url and "newtab" not in url:
                discovered.append(tab)
        return discovered

    def ensure_min_pool(self, min_count: int = 2):
        """确保池中有至少 min_count 个可用标签页"""
        usable = [t for t in self._pool.values()
                  if t.tab_id and t.url and "about:blank" not in t.url]
        while len(usable) < min_count:
            tab = self.create()
            tab.get("about:blank")
            usable.append(tab)

    # ═══════════════════════════════════════════
    # 导航操作
    # ═══════════════════════════════════════════

    @staticmethod
    def navigate(tab, url: str):
        """导航并等待加载"""
        tab.get(url)
        time.sleep(3)

    @staticmethod
    def navigate_hash(tab, hash_str: str):
        """SPA hash 导航"""
        if not hash_str.startswith("#"):
            hash_str = "#" + hash_str
        tab.run_js(f"location.hash='{hash_str}'")
        time.sleep(3)

    # ═══════════════════════════════════════════
    # 清理维护
    # ═══════════════════════════════════════════

    def close_unused(self, keep_tags: list[str] | None = None):
        """关闭不在使用中的标签页"""
        keep = set(keep_tags or list(self._pool.keys()))
        for tag, tab in list(self._pool.items()):
            if tag not in keep:
                try:
                    tab.close()
                except Exception:
                    pass
                del self._pool[tag]
                logger.debug(f"关闭标签页: {tag}")
        # 关闭未管理的杂项标签页
        all_tabs = self.browser.get_tabs()
        pool_ids = {t.tab_id for t in self._pool.values()}
        for tab in all_tabs:
            if tab.tab_id not in pool_ids:
                url = tab.url or ""
                if not self._is_system_tab(url) and url:
                    try:
                        tab.close()
                    except Exception:
                        pass

    @staticmethod
    def _is_system_tab(url: str) -> bool:
        return any(kw in url for kw in [
            "about:", "edge://", "chrome://", "newtab", "ntp.msn.com",
        ])

    # ═══════════════════════════════════════════
    # 信息查询
    # ═══════════════════════════════════════════

    def list_tabs(self) -> list[dict]:
        """列出所有标签页状态"""
        result = []
        for tag, tab in self._pool.items():
            result.append({
                "tag": tag,
                "tab_id": tab.tab_id[:16] if tab.tab_id else "",
                "title": (tab.title or "")[:40],
                "url": (tab.url or "")[:70],
            })
        # 未管理的标签页
        all_tabs = self.browser.get_tabs()
        pool_ids = {t.tab_id for t in self._pool.values()}
        for tab in all_tabs:
            if tab.tab_id not in pool_ids:
                result.append({
                    "tag": "(未管理)",
                    "tab_id": tab.tab_id[:16] if tab.tab_id else "",
                    "title": (tab.title or "")[:4],
                    "url": (tab.url or "")[:70],
                })
        return result

    @property
    def count(self) -> int:
        return len(self._pool)

    # ═══════════════════════════════════════════
    # 释放
    # ═══════════════════════════════════════════

    def close_all(self):
        """关闭所有管理的标签页"""
        for tab in self._pool.values():
            try:
                tab.close()
            except Exception:
                pass
        self._pool.clear()
