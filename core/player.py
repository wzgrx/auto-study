"""
11 — 视频播放层
支持各种播放器：HTML5 video / iframe / CC / Polyv
"""
from __future__ import annotations
import time
import logging
from core.anti_detect import AntiDetect
from core.exceptions import VideoError, VideoNotFoundError, retry

logger = logging.getLogger("player")


class VideoPlayer:
    """视频播放器"""

    def __init__(self, brain):
        self.brain = brain

    @retry(max_attempts=3, delay=60)
    def play(self, tab, course) -> bool:
        AntiDetect.inject(tab)
        info = self._detect(tab)
        if not info:
            raise VideoNotFoundError(f"{course.name}: 未找到视频")
        self._start(tab)
        return self._monitor(tab, course)

    def _detect(self, tab) -> dict | None:
        return self.brain.execute_js(tab, """() => {
            var v = document.querySelector('video');
            if(v && v.duration>0) return {type:'main', duration:v.duration};
            var fs = document.querySelectorAll('iframe');
            for(var f of fs) try {
                var fv = f.contentDocument?.querySelector('video');
                if(fv && fv.duration>0) return {type:'iframe', duration:fv.duration};
            } catch(e){}
            return null;
        }""")

    def _start(self, tab):
        self.brain.execute_js(tab, """
        var v=document.querySelector('video');
        if(!v){var f=document.querySelector('iframe');
            if(f)try{v=f.contentDocument.querySelector('video')}catch(e){}}
        if(v){v.muted=true;v.play();}
        """)

    def _monitor(self, tab, course) -> bool:
        last_pct, stall = 0, 0
        start = time.time()
        while time.time() - start < 86400:
            cur = float(self.brain.execute_js(
                tab, "return document.querySelector('video')?.currentTime||0"))
            dur = float(self.brain.execute_js(
                tab, "return document.querySelector('video')?.duration||0"))
            if dur <= 0:
                stall += 1
                time.sleep(10)
                continue
            pct = cur / dur * 100
            if abs(pct - last_pct) < 0.5:
                stall += 1
            else:
                stall = 0
            last_pct = pct
            if stall > 30:
                logger.warning(f"{course.name}: 播放卡死")
                return False
            AntiDetect.handle_dialogs(tab)
            if pct >= 95:
                time.sleep(30)
                return True
            time.sleep(30)
        return False
