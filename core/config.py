"""
01 — 配置管理
统一管理所有配置：环境变量、账号密码、运行参数、站点策略
"""
from __future__ import annotations
import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """全局配置 — 所有配置集中在此，其他模块通过 Config.xxx 读取

    加载优先级: 默认值 < .env 文件 < 环境变量
    """

    # ── 路径 ──────────────────────────────────────────────
    PROJECT_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = PROJECT_DIR / "data"
    LOG_DIR: Path = PROJECT_DIR / "logs"
    COOKIE_DIR: Path = DATA_DIR / "cookies"
    DOWNLOAD_DIR: Path = DATA_DIR / "downloads"
    RUN_HISTORY_DIR: Path = DATA_DIR / "run_history"

    # ── 浏览器 ────────────────────────────────────────────
    CDP_PORT: int = 9223
    CDP_HOST: str = "localhost"

    # ── 账号管理 ──────────────────────────────────────────
    # 统一字典，每站点一个条目
    # 启动时从环境变量自动填充: CHINAHRT_USER/PASS, HUAYI_USER/PASS
    ACCOUNTS: dict[str, dict[str, str]] = {}

    # ── LLM ────────────────────────────────────────────────
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_MODEL: str = "deepseek-chat"
    GEMMA_URL: str = "http://localhost:8080/v1"

    # ── 运行参数 ──────────────────────────────────────────
    MAX_HOURS: float = 24          # 单次最大运行时长(小时)
    MAX_RETRIES: int = 3           # 失败重试次数
    RETRY_DELAY_SEC: int = 30      # 重试间隔(秒)
    COURSE_COOLDOWN_SEC: int = 60  # 课程间冷却(秒)
    HUMAN_DELAY_SEC: tuple = (1, 3)  # 操作间随机延迟范围(秒)

    # ── 视频播放策略 ──────────────────────────────────────
    # 各平台独立配置，可在 .env 中用 JSON 覆盖
    PLAY_MODE: dict = {
        "chinahrt": {
            "speed": 1.0,
            "segment_mode": "正常",       # 正常 / 三段(每段90s) / 秒播(首尾1s)
            "segment_duration": 90,
            "allow_drag": True,
            "prevent_mouse_leave": True,
        },
        "huayiwang": {
            "speed": 1.0,
            "segment_mode": "正常",
            "parallel_tabs": True,        # 允许多标签页并行播放
            "min_watch_sec": 600,
        },
    }

    # ── 答题 ──────────────────────────────────────────────
    QUIZ_ENABLED: bool = True
    QUIZ_CORRECT_RATE: float = 0.85  # 正确率（随机错题防检测）

    # ── 通知 ──────────────────────────────────────────────
    FEISHU_WEBHOOK: str = ""

    # ═══════════════════════════════════════════════════════
    # 加载
    # ═══════════════════════════════════════════════════════

    _loaded: bool = False

    @classmethod
    def load(cls):
        """加载配置：.env → 环境变量 → 创建目录"""
        if cls._loaded:
            return cls

        # 1. 加载 .env 文件
        env_path = cls.PROJECT_DIR / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        else:
            # 没有 .env 则从 .env.example 复制
            example_path = cls.PROJECT_DIR / ".env.example"
            if example_path.exists():
                print(f"⚠️  未找到 .env 文件，请从 .env.example 复制并填写: cp .env.example .env")

        # 2. 从环境变量读取
        cls._from_env("CDP_PORT", int)
        cls._from_env("CDP_HOST")
        cls._from_env("DEEPSEEK_API_KEY")
        cls._from_env("DEEPSEEK_MODEL")
        cls._from_env("GEMMA_URL")
        cls._from_env("MAX_HOURS", float)
        cls._from_env("MAX_RETRIES", int)
        cls._from_env("RETRY_DELAY_SEC", int)
        cls._from_env("COURSE_COOLDOWN_SEC", int)
        cls._from_env("FEISHU_WEBHOOK")
        cls._from_env("QUIZ_ENABLED", bool)
        cls._from_env("QUIZ_CORRECT_RATE", float)

        # 3. 加载账号
        if os.environ.get("CHINAHRT_USER"):
            cls.ACCOUNTS["chinahrt"] = {
                "user": os.environ.get("CHINAHRT_USER", ""),
                "pass": os.environ.get("CHINAHRT_PASS", ""),
            }
        if os.environ.get("HUAYI_USER"):
            cls.ACCOUNTS["huayiwang"] = {
                "user": os.environ.get("HUAYI_USER", ""),
                "pass": os.environ.get("HUAYI_PASS", ""),
            }

        # 4. 播放策略可被环境变量覆盖
        play_mode_json = os.environ.get("PLAY_MODE")
        if play_mode_json:
            try:
                cls.PLAY_MODE.update(json.loads(play_mode_json))
            except json.JSONDecodeError:
                pass

        # 5. 确保目录存在
        for d in [cls.DATA_DIR, cls.LOG_DIR, cls.COOKIE_DIR,
                  cls.DOWNLOAD_DIR, cls.RUN_HISTORY_DIR]:
            d.mkdir(parents=True, exist_ok=True)

        cls._loaded = True
        return cls

    @classmethod
    def _from_env(cls, key: str, cast: type = str):
        """从环境变量读取配置，如果存在则覆盖"""
        val = os.environ.get(key)
        if val is None:
            return
        if cast == bool:
            setattr(cls, key, val.lower() in ("true", "1", "yes"))
        elif cast == int:
            setattr(cls, key, int(val))
        elif cast == float:
            setattr(cls, key, float(val))
        else:
            setattr(cls, key, val)

    # ═══════════════════════════════════════════════════════
    # 验证
    # ═══════════════════════════════════════════════════════

    @classmethod
    def validate(cls) -> list[str]:
        """检查必要配置，返回缺失项列表"""
        missing = []

        if not cls.DEEPSEEK_API_KEY:
            missing.append("DEEPSEEK_API_KEY")

        if not cls.ACCOUNTS:
            missing.append("账号配置 (CHINAHRT_USER/PASS 或 HUAYI_USER/PASS)")

        # 检测 Gemma 服务是否在线
        if not cls._check_gemma():
            print("⚠️  Gemma 4 (llama-server:8080) 未响应，视觉分析功能不可用")

        return missing

    @classmethod
    def _check_gemma(cls) -> bool:
        """检查 Gemma 4 服务是否在线"""
        try:
            import httpx
            r = httpx.get(f"{cls.GEMMA_URL.replace('/v1', '')}/v1/models",
                          timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    # ═══════════════════════════════════════════════════════
    # 账号快捷方法
    # ═══════════════════════════════════════════════════════

    @classmethod
    def get_account(cls, platform: str) -> dict[str, str] | None:
        """获取指定平台的账号密码"""
        return cls.ACCOUNTS.get(platform)

    @classmethod
    def get_play_mode(cls, platform: str) -> dict:
        """获取指定平台的播放策略"""
        return cls.PLAY_MODE.get(platform, cls.PLAY_MODE.get("chinahrt", {}))

    # ═══════════════════════════════════════════════════════
    # 显示
    # ═══════════════════════════════════════════════════════

    @classmethod
    def display(cls) -> str:
        """打印当前配置（隐藏密码）"""
        lines = ["📋 当前配置:"]
        lines.append(f"   浏览器: Edge:{cls.CDP_PORT}")
        lines.append(f"   账号: {', '.join(cls.ACCOUNTS.keys()) or '未配置'}")
        lines.append(f"   DeepSeek: {'✓' if cls.DEEPSEEK_API_KEY else '✗'}")
        lines.append(f"   Gemma 4: {cls.GEMMA_URL}")
        lines.append(f"   最大运行: {cls.MAX_HOURS}h")
        lines.append(f"   答题: {'开启' if cls.QUIZ_ENABLED else '关闭'}")
        return "\n".join(lines)
