from __future__ import annotations

import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# 녹음 상태
RECORDING = "recording"
PENDING = "pending"
TRANSCRIBING = "transcribing"
DONE = "done"
ERROR = "error"

SCHEMA = """
CREATE TABLE IF NOT EXISTS recordings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    created_at  TEXT    NOT NULL,
    duration    REAL    NOT NULL DEFAULT 0,
    file_path   TEXT    NOT NULL,
    status      TEXT    NOT NULL,
    model       TEXT,
    error       TEXT,
    transcript  TEXT    NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_recordings_created ON recordings(created_at DESC);
CREATE TABLE IF NOT EXISTS segments (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    recording_id  INTEGER NOT NULL REFERENCES recordings(id) ON DELETE CASCADE,
    start         REAL    NOT NULL,
    end           REAL    NOT NULL,
    text          TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_segments_rec ON segments(recording_id, start);
CREATE TABLE IF NOT EXISTS settings (
    key    TEXT PRIMARY KEY,
    value  TEXT NOT NULL
);
"""


@dataclass
class Recording:
    id: int
    title: str
    created_at: datetime
    duration: float
    file_path: Path
    status: str
    model: str | None
    error: str | None
    transcript: str


@dataclass
class Segment:
    start: float
    end: float
    text: str


def _escape_like(s: str) -> str:
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class Database:
    """스레드마다 별도 커넥션을 쓴다 (변환 작업은 백그라운드 스레드에서 기록)."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self._local = threading.local()
        with self._conn() as c:
            c.executescript(SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(self.path, timeout=10)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            self._local.conn = conn
        return conn

    def close(self) -> None:
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            conn.close()
            self._local.conn = None

    @staticmethod
    def _row(r: sqlite3.Row) -> Recording:
        return Recording(
            id=r["id"], title=r["title"], created_at=datetime.fromisoformat(r["created_at"]),
            duration=r["duration"], file_path=Path(r["file_path"]), status=r["status"],
            model=r["model"], error=r["error"], transcript=r["transcript"],
        )

    # --- recordings ---
    def create_recording(self, title: str, file_path: Path, created_at: datetime) -> int:
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO recordings (title, created_at, file_path, status) VALUES (?, ?, ?, ?)",
                (title, created_at.isoformat(timespec="seconds"), str(file_path), RECORDING),
            )
            return cur.lastrowid

    def get(self, rec_id: int) -> Recording | None:
        r = self._conn().execute("SELECT * FROM recordings WHERE id = ?", (rec_id,)).fetchone()
        return self._row(r) if r else None

    def list(self, query: str = "", limit: int = 20, offset: int = 0) -> list[Recording]:
        where, params = self._search_clause(query)
        rows = self._conn().execute(
            f"SELECT * FROM recordings {where} ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?",
            (*params, limit, offset),
        ).fetchall()
        return [self._row(r) for r in rows]

    def count(self, query: str = "") -> int:
        where, params = self._search_clause(query)
        return self._conn().execute(f"SELECT COUNT(*) FROM recordings {where}", params).fetchone()[0]

    @staticmethod
    def _search_clause(query: str) -> tuple[str, tuple]:
        query = query.strip()
        if not query:
            return "", ()
        pat = f"%{_escape_like(query)}%"
        return "WHERE title LIKE ? ESCAPE '\\' OR transcript LIKE ? ESCAPE '\\'", (pat, pat)

    def ids_with_status(self, *statuses: str) -> list[int]:
        marks = ",".join("?" * len(statuses))
        rows = self._conn().execute(
            f"SELECT id FROM recordings WHERE status IN ({marks}) ORDER BY created_at, id", statuses
        ).fetchall()
        return [r[0] for r in rows]

    def update(self, rec_id: int, **fields) -> None:
        allowed = {"title", "duration", "status", "model", "error", "transcript"}
        bad = set(fields) - allowed
        if bad:
            raise ValueError(f"알 수 없는 필드: {bad}")
        cols = ", ".join(f"{k} = ?" for k in fields)
        with self._conn() as c:
            c.execute(f"UPDATE recordings SET {cols} WHERE id = ?", (*fields.values(), rec_id))

    def delete(self, rec_id: int) -> None:
        with self._conn() as c:
            c.execute("DELETE FROM recordings WHERE id = ?", (rec_id,))

    # --- segments ---
    def save_transcript(self, rec_id: int, segments: list[Segment], model: str) -> None:
        text = "\n".join(s.text for s in segments)
        with self._conn() as c:
            c.execute("DELETE FROM segments WHERE recording_id = ?", (rec_id,))
            c.executemany(
                "INSERT INTO segments (recording_id, start, end, text) VALUES (?, ?, ?, ?)",
                [(rec_id, s.start, s.end, s.text) for s in segments],
            )
            c.execute(
                "UPDATE recordings SET transcript = ?, status = ?, model = ?, error = NULL WHERE id = ?",
                (text, DONE, model, rec_id),
            )

    def segments(self, rec_id: int) -> list[Segment]:
        rows = self._conn().execute(
            "SELECT start, end, text FROM segments WHERE recording_id = ? ORDER BY start", (rec_id,)
        ).fetchall()
        return [Segment(r[0], r[1], r[2]) for r in rows]

    # --- settings ---
    def get_setting(self, key: str, default: str | None = None) -> str | None:
        r = self._conn().execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return r[0] if r else default

    def set_setting(self, key: str, value: str) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )
