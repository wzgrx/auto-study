"""
06 — 反检测层
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
        tab.run_js("""
        Object.defineProperty(navigator, 'webdriver', {get:()=>undefined});
        Object.defineProperty(navigator, 'plugins', {get:()=>[1,2,3,4,5]});
        Object.defineProperty(navigator, 'languages', {get:()=>['zh-CN','zh','en']});
        """)

    @staticmethod
    def handle_dialogs(tab) -> bool:
        return tab.run_js("""
        var closed = false;
        var kws = ['继续','确定','确认','已完成','下一节','知道了','好的','关闭'];
        var btns = document.querySelectorAll('button,.el-button,.layui-layer-btn a');
        for(var b of btns){
            var t=b.textContent.trim();
            for(var k of kws){if(t.includes(k)){b.click();closed=true;break;}}
            if(closed)break;
        }
        return closed;
        """)

    @staticmethod
    def hijack_playback_rate(tab):
        """华医网防检测倍速：对外显示1.0x，实际可任意"""
        tab.run_js("""
        if(window.__rateHijacked) return;
        var desc=Object.getOwnPropertyDescriptor(HTMLMediaElement.prototype,'playbackRate');
        Object.defineProperty(HTMLMediaElement.prototype,'playbackRate',{
            get:function(){return 1.0;},
            set:function(v){if(v>0)desc.set.call(this,v);}
        });
        Object.defineProperty(HTMLMediaElement.prototype,'playbackRate',{configurable:true});
        window.__rateHijacked=true;
        """)

    @staticmethod
    def random_delay():
        time.sleep(random.uniform(*Config.HUMAN_DELAY_SEC))

    @staticmethod
    def prevent_mouse_leave(tab):
        tab.run_js("""
        document.addEventListener('visibilitychange',function(e){e.stopPropagation()},true);
        window.addEventListener('blur',function(e){e.stopPropagation()},true);
        """)
