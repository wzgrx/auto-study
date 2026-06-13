"""
02 - 标签页管理器
3个固定标签页的管理：创建、识别、重连、清理
Tab1=课程列表, Tab2=课程详情, Tab3=视频播放
"""
from __future__ import annotations
import time
import logging
from DrissionPage import Chromium
from core.config import Config

logger = logging.getLogger("tab_manager")


class TabManager:
    """3固定标签页管理器

    职责：
    - 连接已有 Edge (CDP 9223)
    - 维持3个固定标签页（Tab1/Tab2/Tab3）
    - 按角色（role）识别标签页，而非索引
    - 导航后自动重连 WebSocket
    - 清理多余标签页
    """

    # 三个标签页的角色定义
    ROLES = ["tab1", "tab2", "tab3"]

    def __init__(self):
        self.browser: Chromium = Chromium(addr=Config.CDP_PORT)
        self._tabs: dict[str, Chromium] = {}  # {role: Tab对象}
        self._identify_tabs()
        logger.info(f"浏览器已连接: Edge:{Config.CDP_PORT}")

    # ── 标签页识别 ──

    def _identify_tabs(self):
        """自动识别已有标签页，按角色分配"""
        all_tabs = self.browser.get_tabs()
        chinahrt_tabs = [t for t in all_tabs if "chinahrt" in (t.url or "")]
        other_tabs = [t for t in all_tabs if t not in chinahrt_tabs]

        # 按特征分配角色
        for tab in chinahrt_tabs:
            url = tab.url or ""
            if "v_selected_course" in url or "v_trainplan" in url:
                self._tabs["tab1"] = tab
            elif "v_courseDetails" in url:
                self._tabs["tab2"] = tab
            elif "v_video" in url or "vuelogin" in url:
                self._tabs["tab3"] = tab

        # 补全缺失的标签页
        for role in self.ROLES:
            if role not in self._tabs:
                self._tabs[role] = self.browser.new_tab()
                logger.info(f"新建标签页: {role}")

        logger.info(f"标签页就绪: tab1={self._tabs['tab1'].url[:50]}, "
                     f"tab2={self._tabs['tab2'].url[:50]}, "
                     f"tab3={self._tabs['tab3'].url[:50]}")

    # ── 获取标签页 ──

    def get(self, role: str):
        """按角色获取标签页，断线自动重连"""
        tab = self._tabs.get(role)
        if not tab:
            raise RuntimeError(f"标签页 {role} 不存在")
        return tab

    def get_all(self) -> dict[str, Chromium]:
        return dict(self._tabs)

    # ── 标签页管理 ──

    def navigate(self, role: str, url: str):
        """导航并等待加载"""
        tab = self.get(role)
        tab.get(url)
        time.sleep(3)
        # 导航后重新获取标签页引用（SPA可能会创建新target）
        self._refresh_tab_ref(role)

    def navigate_hash(self, role: str, hash_str: str):
        """SPA hash 导航"""
        tab = self.get(role)
        if not hash_str.startswith("#"):
            hash_str = "#" + hash_str
        tab.run_js(f"location.hash='{hash_str}'")
        time.sleep(3)

    def close_extra(self):
        """关闭多余的标签页，只保留我们的3个"""
        all_tabs = self.browser.get_tabs()
        our_ids = {t.id for t in self._tabs.values()}
        for tab in all_tabs:
            if tab.id not in our_ids:
                try:
                    tab.close()
                except Exception:
                    pass

    # ── 刷新标签页引用（导航/断线后）──

    def _refresh_tab_ref(self, role: str):
        """导航后重新获取标签页对象"""
        old_tab = self._tabs.get(role)
        if not old_tab:
            return
        old_id = old_tab.id
        # 等待新标签页出现
        for _ in range(10):
            all_tabs = self.browser.get_tabs()
            for tab in all_tabs:
                if tab.id == old_id:
                    self._tabs[role] = tab
                    return
            time.sleep(1)
        # 如果旧标签页没了，新建一个
        self._tabs[role] = self.browser.new_tab()
        logger.warning(f"{role} 标签页已重建")

    # ── 关闭释放 ──

    def close(self):
        for tab in self._tabs.values():
            try:
                tab.close()
            except Exception:
                pass
        self._tabs.clear()
