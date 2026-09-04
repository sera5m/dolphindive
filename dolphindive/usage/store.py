from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
import time


def default_db_path() -> Path:
    base = Path.home() / ".local" / "share" / "dolphindive"
    base.mkdir(parents=True, exist_ok=True)
    return base / "usage.sqlite"


@dataclass
class Usage:
    opens: int = 0
    last_open: float = 0.0


class UsageStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_db_path()
        self._conn = sqlite3.connect(self.path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS usage (
                path TEXT PRIMARY KEY,
                opens INTEGER NOT NULL DEFAULT 0,
                last_open REAL NOT NULL DEFAULT 0
            )
            """
        )
        self._conn.commit()

    def get(self, path: str) -> Usage:
        row = self._conn.execute(
            "SELECT opens, last_open FROM usage WHERE path = ?", (path,)
        ).fetchone()
        if not row:
            return Usage()
        return Usage(opens=row[0], last_open=row[1])

    def record_open(self, path: str) -> None:
        now = time.time()
        self._conn.execute(
            """
            INSERT INTO usage(path, opens, last_open) VALUES(?, 1, ?)
            ON CONFLICT(path) DO UPDATE SET
                opens = opens + 1,
                last_open = excluded.last_open
            """,
            (path, now),
        )
        self._conn.commit()
