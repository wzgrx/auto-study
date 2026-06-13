"""
15 - 进度管理层
持久化记录课程进度
"""
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
from core.config import Config

logger = __import__("logging").getLogger("progress")


class ProgressManager:
    """进度管理器"""

    def __init__(self):
        self.db_path = Config.DATA_DIR / "progress.json"
        self._data = self._load()

    def _load(self) -> dict:
        if self.db_path.exists():
            return json.loads(self.db_path.read_text())
        return {"courses": {}, "history": []}

    def save(self, course_id: str, progress: float, status: str = "进行中"):
        self._data["courses"][course_id] = {
            "progress": progress, "status": status,
            "updated_at": datetime.now().isoformat(),
        }
        self._flush()

    def get_remaining(self) -> list:
        return [c for c in self._data["courses"].values()
                if c["progress"] < 100 and c["status"] != "跳过"]

    def _flush(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2))
