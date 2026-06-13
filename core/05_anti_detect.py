"""
05 - 反检测层
防机器人检测、弹窗处理、倍速劫持
"""
from __future__ import annotations
import time
import random
import logging
from core.config import Config

logger = logging.getLogger("anti_detect")


class AntiDetect:

    @staticmethod
    def inject(tab):
        """注入反检测JS"""
        tab.run_js("""
        Object.defineProperty(navigator, 'webdriver', {get:()=>undefined});
        Object.defineProperty(navigator, 'plugins', {get:()=>[1,2,3,4,5]});
        Object.defineProperty(navigator, 'languages', {get:()=>['zh-CN','zh','en']});
        """)
        logger.debug("反检测JS已注入")

    @staticmethod
    def handle_dialogs(tab) -> bool:
        """扫描并关闭弹窗"""
        return tab.run_js("""
        var closed = false;
        var keywords = ['继续','确定','确认','已完成','下一节','知道了','好的'];
        var btns = document.querySelectorAll('button,.el-button,.layui-layer-btn a');
        for(var b of btns) {
            var t = b.textContent.trim();
            for(var k of keywords){
                if(t.includes(k)){ b.click(); closed = true; break; }
            }
            if(closed) break;
        }
        return closed;
        """)

    @staticmethod
    def hijack_playback_rate(tab):
        """劫持 playbackRate（华医网防检测倍速）"""
        tab.run_js("""
        if(window.__rateHijacked) return;
        var desc = Object.getOwnPropertyDescriptor(HTMLMediaElement.prototype, 'playbackRate');
        Object.defineProperty(HTMLMediaElement.prototype, 'playbackRate', {
            get: function(){ return 1.0; },
            set: function(v){ if(v>0) desc.set.call(this, v); }
        });
        window.__rateHijacked = true;
        """)
        logger.debug("倍速劫持已注入")

    @staticmethod
    def random_delay():
        time.sleep(random.uniform(*Config.HUMAN_DELAY))
