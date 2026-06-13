"""
01 - 配置管理
统一管理所有配置：环境变量、账号、运行参数
"""
from __future__ import annotations
import os
from pathlib import Path


class Config:
    """全局配置 — 所有配置集中在此"""

    # 浏览器
    CDP_PORT: int = int(os.environ.get("CDP_PORT", "9223"))
    CDP_HOST: str = os.environ.get("CDP_HOST", "localhost")

    # 宁夏继续教育
    CHINAHRT_USER: str = os.environ.get("CHINAHRT_USER", "")
    CHINAHRT_PASS: str = os.environ.get("CHINAHRT_PASS", "")

    # 华医网
    HUAYI_USER: str = os.environ.get("HUAYI_USER", "")
    HUAYI_PASS: str = os.environ.get("HUAYI_PASS", "")

    # LLM
    DEEPSEEK_API_KEY: str = os.environ.get("DEEPSEEK_API_KEY", "")
    DEEPSEEK_MODEL: str = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
    GEMMA_URL: str = os.environ.get("GEMMA_URL", "http://localhost:8080/v1")

    # 运行
    MAX_HOURS: float = float(os.environ.get("MAX_HOURS", "24"))
    MAX_RETRIES: int = int(os.environ.get("MAX_RETRIES", "3"))
    RETRY_DELAY: int = int(os.environ.get("RETRY_DELAY", "30"))
    COURSE_COOLDOWN: int = int(os.environ.get("COURSE_COOLDOWN", "60"))
    HUMAN_DELAY: tuple = (1, 3)

    # 播放策略（各平台不同）
    PLAY_MODE: dict = {
        "chinahrt": {"speed": 1.0, "segment_mode": "正常", "allow_drag": True},
        "huayiwang": {"speed": 1.0, "segment_mode": "正常", "parallel_tabs": True},
    }

    # 答题
    QUIZ_ENABLED: bool = os.environ.get("QUIZ_ENABLED", "true").lower() == "true"
    QUIZ_CORRECT_RATE: float = float(os.environ.get("QUIZ_CORRECT_RATE", "0.85"))

    # 通知
    FEISHU_WEBHOOK: str = os.environ.get("FEISHU_WEBHOOK", "")

    # 路径
    PROJECT_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = PROJECT_DIR / "data"
    LOG_DIR: Path = PROJECT_DIR / "logs"
    COOKIE_DIR: Path = DATA_DIR / "cookies"
    DOWNLOAD_DIR: Path = DATA_DIR / "downloads"
    RUN_HISTORY_DIR: Path = DATA_DIR / "run_history"

    @classmethod
    def load(cls):
        """从 .env 和环境变量加载配置"""
        from dotenv import load_dotenv
        env_path = cls.PROJECT_DIR / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        # 确保目录存在
        for d in [cls.DATA_DIR, cls.LOG_DIR, cls.COOKIE_DIR,
                  cls.DOWNLOAD_DIR, cls.RUN_HISTORY_DIR]:
            d.mkdir(parents=True, exist_ok=True)
        return cls

    @classmethod
    def validate(cls) -> list[str]:
        """检查必要配置是否齐全，返回缺失项列表"""
        missing = []
        if not cls.DEEPSEEK_API_KEY:
            missing.append("DEEPSEEK_API_KEY")
        if not cls.CHINAHRT_USER or not cls.CHINAHRT_PASS:
            missing.append("CHINAHRT_USER/PASS")
        return missing
