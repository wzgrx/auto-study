"""
02 - 日志系统
统一日志处理，控制台 + 文件轮转
"""
import logging, sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from core.config import Config


def setup_logger(name: str = "auto-study") -> logging.Logger:
    """配置并返回日志器"""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # 控制台
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(
        "[%(asctime)s] [%(name)s] %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(console)

    # 文件
    log_dir = Config.LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    fh = RotatingFileHandler(
        log_dir / "run.log", maxBytes=5 * 1024 * 1024, backupCount=7, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"))
    logger.addHandler(fh)

    return logger
