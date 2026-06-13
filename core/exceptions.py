"""
04 — 异常体系 + 重试装饰器
所有模块的异常基类 + @retry 失败自动重试
"""
from __future__ import annotations
import asyncio
import time
import logging
from functools import wraps
from typing import Union, Type

logger = logging.getLogger("exceptions")


# ═════════════════════════════════════════════════════════
# 异常体系
# ═════════════════════════════════════════════════════════

class AutoStudyError(Exception):
    """所有异常基类。捕获这个 = 捕获所有已知错误"""


# ── 浏览器/连接 ──
class BrowserError(AutoStudyError):
    """浏览器连接/操作异常"""

class TabError(BrowserError):
    """标签页操作异常"""


# ── 登录 ──
class LoginError(AutoStudyError):
    """登录失败"""

class CaptchaError(LoginError):
    """验证码识别失败"""

class CredentialError(LoginError):
    """凭据缺失或错误"""


# ── 课程 ──
class CourseScanError(AutoStudyError):
    """课程识别失败"""

class CourseEmptyError(CourseScanError):
    """没有需要刷的课程"""


# ── 播放 ──
class VideoError(AutoStudyError):
    """视频播放异常"""

class VideoNotFoundError(VideoError):
    """未找到视频元素"""

class VideoStallError(VideoError):
    """视频播放卡死"""


# ── 答题 ──
class QuizError(AutoStudyError):
    """答题异常"""


# ── 通用 ──
class TimeoutError(AutoStudyError):
    """操作超时"""

class HumanIntervention(AutoStudyError):
    """需要人工介入 —— 框架无法自动处理，通知用户"""


# ═════════════════════════════════════════════════════════
# @retry 装饰器
# ═════════════════════════════════════════════════════════

def retry(max_attempts: int = 3, delay: float = 30,
          on_exception: type | tuple = AutoStudyError):
    """失败自动重试装饰器

    用法:
        @retry(max_attempts=3, delay=30)
        def login(): ...

        @retry(max_attempts=5, delay=10)
        async def play_video(): ...

    参数:
        max_attempts: 最大重试次数
        delay: 重试间隔秒数
        on_exception: 捕获的异常类型（默认所有 AutoStudyError）
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except on_exception as e:
                    last_exc = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"⏳ 重试 {attempt}/{max_attempts}: {e}")
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"❌ 重试耗尽 ({max_attempts}次): {e}")
            raise last_exc

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except on_exception as e:
                    last_exc = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"⏳ 重试 {attempt}/{max_attempts}: {e}")
                        time.sleep(delay)
                    else:
                        logger.error(f"❌ 重试耗尽 ({max_attempts}次): {e}")
            raise last_exc

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


# ═════════════════════════════════════════════════════════
# HumanIntervention 信号
# ═════════════════════════════════════════════════════════

_HUMAN_CALLBACK = None


def set_human_callback(callback):
    """注册人工介入回调（由 scheduler 注入）"""
    global _HUMAN_CALLBACK
    _HUMAN_CALLBACK = callback


def ask_human(question: str) -> str:
    """触发人工介入：通知用户并等待输入"""
    if _HUMAN_CALLBACK:
        return _HUMAN_CALLBACK(question)
    raise HumanIntervention(question)
