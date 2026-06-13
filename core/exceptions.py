"""
03 - 异常体系 + 重试装饰器
"""
from __future__ import annotations
import time
import logging
from functools import wraps

logger = logging.getLogger("exceptions")


class AutoStudyError(Exception):
    """所有异常基类"""


class LoginError(AutoStudyError):
    """登录失败"""


class CaptchaError(LoginError):
    """验证码识别失败"""


class CourseScanError(AutoStudyError):
    """课程识别失败"""


class VideoError(AutoStudyError):
    """视频播放异常"""


class QuizError(AutoStudyError):
    """答题异常"""


class TimeoutError(AutoStudyError):
    """操作超时"""


class HumanIntervention(AutoStudyError):
    """需要人工介入"""


def retry(max_attempts=3, delay=30, on_exception=None):
    """失败自动重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except AutoStudyError as e:
                    last_exc = e
                    if attempt < max_attempts:
                        logger.warning(f"重试 {attempt}/{max_attempts}: {e}")
                        time.sleep(delay)
                    else:
                        logger.error(f"重试耗尽: {e}")
            raise last_exc
        return wrapper
    return decorator
