"""
10 - 视频播放层
支持各种播放器：HTML5 video / iframe / CC播放器 / Polyv
"""
from __future__ import annotations
import time
import logging
from core.brain import BrowserBrain
from core.anti_detect import AntiDetect
from core.exceptions import VideoError, retry
from core.config import Config

logger = logging.getLogger("player")


class VideoPlayer:
    """视频播放器"""

    def __init__(self, brain: BrowserBrain):
        self.brain = brain

    @retry(max_attempts=3, delay=60)
    def play(self, tab, course) -> bool:
        """播放课程视频直到完成"""
        AntiDetect.inject(tab)

        info = self._detect_video(tab)
        if not info:
            logger.warning(f"{course.name}: 未找到视频")
            return False

        self._start_playback(tab, info)
        return self._monitor_progress(tab, course)

    def _detect_video(self, tab) -> dict:
        """检测视频元素"""
        js = """() => {
            var v = document.querySelector('video');
            if(v && v.duration > 0) return {type:'main', duration:v.duration};
            var frames = document.querySelectorAll('iframe');
            for(var f of frames) {
                try {
                    var fv = f.contentDocument?.querySelector('video');
                    if(fv && fv.duration > 0) return {type:'iframe', duration:fv.duration};
                } catch(e) {}
            }
            return null;
        }"""
        return self.brain.execute_js(tab, js)

    def _start_playback(self, tab, info):
        tab.run_js("""
        var v = document.querySelector('video');
        if(!v) { var f = document.querySelector('iframe');
            if(f) try { v = f.contentDocument.querySelector('video'); } catch(e) {} }
        if(v) { v.muted = true; v.play(); }
        """)

    def _monitor_progress(self, tab, course) -> bool:
        """监控播放进度"""
        start = time.time()
        stall_count = 0
        last_progress = 0

        while time.time() - start < Config.MAX_HOURS * 3600:
            AntiDetect.handle_dialogs(tab)
            current = self._get_current(tab)
            duration = self._get_duration(tab)
            if duration <= 0:
                stall_count += 1
                time.sleep(10)
                continue
            progress = current / duration * 100
            if abs(progress - last_progress) < 0.5:
                stall_count += 1
            else:
                stall_count = 0
            last_progress = progress
            if stall_count > 30:
                logger.warning("播放卡死，跳过")
                return False
            if progress >= 95:
                time.sleep(30)
                return True
            time.sleep(30)
        return False

    def _get_current(self, tab) -> float:
        return float(self.brain.execute_js(tab, "return document.querySelector('video')?.currentTime || 0"))

    def _get_duration(self, tab) -> float:
        return float(self.brain.execute_js(tab, "return document.querySelector('video')?.duration || 0"))
