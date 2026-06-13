"""
03 — 日志系统
统一日志处理：控制台(INFO+颜色) + 文件轮转(DEBUG)
所有模块通过 logging.getLogger("模块名") 使用
"""
from __future__ import annotations
import sys
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from core.config import Config


# 控制台颜色
_LOG_COLORS = {
    "DEBUG": "\033[36m",     # 青色
    "INFO": "\033[32m",      # 绿色
    "WARNING": "\033[33m",   # 黄色
    "ERROR": "\033[31m",     # 红色
    "CRITICAL": "\033[35m",  # 紫色
    "RESET": "\033[0m",
}


class ColoredFormatter(logging.Formatter):
    """控制台彩色输出"""

    def format(self, record):
        level = record.levelname
        color = _LOG_COLORS.get(level, _LOG_COLORS["RESET"])
        reset = _LOG_COLORS["RESET"]
        record.levelname = f"{color}{level}{reset}"
        return super().format(record)


def setup_logger(name: str = "auto-study") -> logging.Logger:
    """配置并返回日志器

    调用方:
        logger = logging.getLogger("模块名")

    输出:
        - 控制台: INFO 级别, 彩色
        - 文件 run.log: DEBUG 级别, 5MB 轮转, 保留7天
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # ── 控制台 Handler ──
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(ColoredFormatter(
        "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(console)

    # ── 文件 Handler ──
    log_dir = Config.LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_dir / "run.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=7,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
    ))
    logger.addHandler(file_handler)

    return logger
