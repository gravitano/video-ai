"""Persistent run state (.scene/state.json) and the paid-call ledger (.scene/ledger.jsonl).

State is written after every mutation so a crashed run can resume: a submitted
video task_id is recorded *before* polling, and never re-submitted for the same key.
"""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path


class State:
    def __init__(self, root: Path):
        self.dir = root / ".scene"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.path = self.dir / "state.json"
        self._lock = threading.Lock()
        self.data: dict = json.loads(self.path.read_text()) if self.path.exists() else {}

    def section(self, name: str) -> dict:
        return self.data.setdefault(name, {})

    def get(self, section: str, key: str, default=None):
        return self.data.get(section, {}).get(key, default)

    def put(self, section: str, key: str, value) -> None:
        with self._lock:
            self.data.setdefault(section, {})[key] = value
            self._save()

    def update(self, section: str, key: str, **fields) -> dict:
        with self._lock:
            entry = self.data.setdefault(section, {}).setdefault(key, {})
            entry.update(fields)
            self._save()
            return entry

    def _save(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, indent=1, ensure_ascii=False))
        os.replace(tmp, self.path)


class Ledger:
    """Append-only record of every paid (or would-be paid) provider call."""

    def __init__(self, root: Path):
        self.path = root / ".scene" / "ledger.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def add(self, **entry) -> None:
        entry = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), **entry}
        with self._lock, open(self.path, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def entries(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text().splitlines() if line.strip()]

    def spent(self, kind: str | None = None) -> float:
        return round(sum(e.get("usd", 0.0) for e in self.entries()
                         if e.get("event") == "submitted" and (kind is None or e.get("kind") == kind)), 4)
