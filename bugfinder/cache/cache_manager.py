from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any


class CacheManager:
    def __init__(self, db_path: str = ".bugfinder_cache.sqlite3") -> None:
        self.db_path = db_path
        self._conn = sqlite3.connect(self.db_path)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_cache (
                cache_key TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    @staticmethod
    def build_hash(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def get(self, cache_key: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT payload FROM analysis_cache WHERE cache_key = ?",
            (cache_key,),
        ).fetchone()
        if not row:
            return None
        return json.loads(row[0])

    def set(self, cache_key: str, payload: dict[str, Any]) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO analysis_cache(cache_key, payload) VALUES (?, ?)",
            (cache_key, json.dumps(payload)),
        )
        self._conn.commit()

    @staticmethod
    def cache_key(file_path: str, model: str, provider: str, content: str) -> str:
        return f"{provider}:{model}:{file_path}:{CacheManager.build_hash(content)}"

    @staticmethod
    def read_file(file_path: Path) -> str:
        return file_path.read_text(encoding="utf-8", errors="ignore")
