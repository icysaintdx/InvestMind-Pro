from __future__ import annotations

import hashlib
import json
import threading
import time
from pathlib import Path
from typing import Dict, Optional


class DedupStore:
    def __init__(self, ttl_seconds: int, cache_file: str = "data/realtime_flash/dedup_cache.json", max_cache_size: int = 20000):
        self.ttl_seconds = max(1, int(ttl_seconds))
        self.max_cache_size = max(100, int(max_cache_size))
        self.cache_path = Path(cache_file)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._items: Dict[str, float] = {}
        self._load()

    @staticmethod
    def fingerprint(item: Dict) -> str:
        title = (item.get("title") or "").strip()
        content = (item.get("content") or "").strip()
        source = (item.get("source") or "").strip()
        publish_time = (item.get("publish_time") or "").strip()
        source_key = (item.get("source_key") or "").strip()
        raw = f"{source}|{source_key}|{publish_time}|{title}|{content}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _load(self) -> None:
        if not self.cache_path.exists():
            return
        try:
            content = self.cache_path.read_text(encoding="utf-8")
            data = json.loads(content)
            now = time.time()
            for k, v in data.items():
                if isinstance(v, (int, float)) and (now - float(v)) <= self.ttl_seconds:
                    self._items[k] = float(v)
        except Exception:
            self._items = {}

    def _prune_locked(self) -> None:
        now = time.time()
        expired = [k for k, ts in self._items.items() if (now - ts) > self.ttl_seconds]
        for k in expired:
            self._items.pop(k, None)
        if len(self._items) > self.max_cache_size:
            sorted_items = sorted(self._items.items(), key=lambda x: x[1], reverse=True)
            keep = dict(sorted_items[: self.max_cache_size])
            self._items = keep

    def contains(self, fp: str) -> bool:
        with self._lock:
            ts: Optional[float] = self._items.get(fp)
            if ts is None:
                return False
            if (time.time() - ts) > self.ttl_seconds:
                self._items.pop(fp, None)
                return False
            return True

    def mark(self, fp: str) -> None:
        with self._lock:
            self._items[fp] = time.time()
            self._prune_locked()

    def save(self) -> None:
        with self._lock:
            self._prune_locked()
            payload = json.dumps(self._items, ensure_ascii=False)
            self.cache_path.write_text(payload, encoding="utf-8")

    def size(self) -> int:
        with self._lock:
            return len(self._items)
