"""Сохранение прогресса в ~/.netlab/progress.json (или в $NETLAB_HOME)."""
from __future__ import annotations

import json
import os
from pathlib import Path


def default_path() -> Path:
    base = os.environ.get("NETLAB_HOME")
    return (Path(base) if base else Path.home() / ".netlab") / "progress.json"


class Progress:
    def __init__(self, path: Path, data: dict | None = None):
        self.path = path
        self.data = data or {}
        self.data.setdefault("lessons", {})
        self.data.setdefault("exam_best", 0.0)
        self.listeners = []

    @classmethod
    def load(cls, path: Path | None = None) -> "Progress":
        path = path or default_path()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                data = {}
        except (OSError, ValueError):
            data = {}
        return cls(path, data)

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(self.path)
        except OSError:
            pass
        for cb in list(self.listeners):
            try:
                cb()
            except Exception:  # noqa: BLE001 — слушатель не должен ломать сохранение
                pass

    def lesson(self, key: str) -> dict:
        entry = self.data["lessons"].setdefault(key, {})
        entry.setdefault("theory", False)
        entry.setdefault("anims", [])
        entry.setdefault("tasks", 0)
        entry.setdefault("quiz", 0.0)
        return entry

    def mark_theory(self, key: str):
        e = self.lesson(key)
        if not e["theory"]:
            e["theory"] = True
            self.save()

    def mark_anim(self, key: str, title: str):
        e = self.lesson(key)
        if title not in e["anims"]:
            e["anims"].append(title)
            self.save()

    def add_task(self, key: str):
        self.lesson(key)["tasks"] += 1
        self.save()

    def set_quiz(self, key: str, ratio: float):
        e = self.lesson(key)
        if ratio > e["quiz"]:
            e["quiz"] = round(ratio, 3)
            self.save()

    def set_exam(self, ratio: float):
        if ratio > self.data["exam_best"]:
            self.data["exam_best"] = round(ratio, 3)
            self.save()

    def percent(self, key: str, total_anims: int) -> int:
        e = self.lesson(key)
        anim = min(1.0, len(e["anims"]) / total_anims) if total_anims else 1.0
        score = 0.15 * e["theory"] + 0.30 * anim + 0.20 * min(e["tasks"], 5) / 5 + 0.35 * e["quiz"]
        return round(score * 100)

    def reset(self):
        self.data = {"lessons": {}, "exam_best": 0.0}
        self.save()
