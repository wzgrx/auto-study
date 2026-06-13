"""
16 — 进度管理层
持久化记录课程进度
"""
from __future__ import annotations
import json
from datetime import datetime
from core.config import Config

logger = __import__("logging").getLogger("progress")


class ProgressManager:
    """进度管理器"""

    def __init__(self):
        self.path = Config.DATA_DIR / "progress.json"
        self._data = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            return json.loads(self.path.read_text(encoding="utf-8"))
        return {"courses": {}, "history": []}

    def save(self, course_id: str, progress: float, status: str = "进行中"):
        self._data["courses"][course_id] = {
            "progress": progress, "status": status,
            "updated_at": datetime.now().isoformat(),
        }
        self._flush()

    def get(self, course_id: str) -> dict | None:
        return self._data["courses"].get(course_id)

    def get_remaining(self) -> list[dict]:
        return [c for c in self._data["courses"].values()
                if c["progress"] < 100 and c["status"] != "跳过"]

    def stats(self) -> dict:
        courses = self._data["courses"].values()
        total = len(courses)
        done = sum(1 for c in courses if c["progress"] >= 100)
        return {"total": total, "completed": done,
                "rate": done / total * 100 if total else 0}

    def _flush(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2),
            encoding="utf-8")
