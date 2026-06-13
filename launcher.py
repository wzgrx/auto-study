#!/usr/bin/env python3
"""
Auto-Study CLI 入口
用法:
    python3 launcher.py chinahrt --auto
    python3 launcher.py huayiwang --step
"""
from __future__ import annotations
import sys
import argparse
from pathlib import Path

# 确保 core 在导入路径
sys.path.insert(0, str(Path(__file__).parent))

from core.config import Config
from core.logger import setup_logger
from core.scheduler import Scheduler


def main():
    parser = argparse.ArgumentParser(description="全能刷课平台")
    parser.add_argument("platform", choices=["chinahrt", "huayiwang"], help="刷课平台")
    parser.add_argument("mode", choices=["auto", "step", "cron"], default="auto", nargs="?",
                        help="运行模式: auto全自动 / step步进 / cron定时")
    parser.add_argument("--max-steps", type=int, default=100, help="最大步数")
    args = parser.parse_args()

    # 初始化
    Config.load()
    logger = setup_logger()
    logger.info(f"启动: {args.platform} @ {args.mode} 模式")

    # 检查配置
    missing = Config.validate()
    if missing:
        logger.warning(f"缺少配置: {', '.join(missing)}")

    # 运行
    scheduler = Scheduler()
    if args.mode == "auto":
        scheduler.auto(args.platform, "", "")
    elif args.mode == "step":
        scheduler.step("")
    elif args.mode == "cron":
        scheduler.cron(args.platform, "0 2 * * *")


if __name__ == "__main__":
    main()
