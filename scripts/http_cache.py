from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from datetime import datetime
from typing import Dict, Optional


DB_PATH = os.path.join("data", "http_cache.sqlite")


def _ensure_dir() -> None:
    os.makedirs("data", exist_ok=True)


class HttpCache:
    def __init__(self, path: Optional[str] = None) -> None:
        self.path = path or DB_PATH
        _ensure_dir()
        with closing(sqlite3.connect(self.path)) as conn:
            with conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS http_cache (
                      url TEXT PRIMARY KEY,
                      etag TEXT,
                      last_modified TEXT,
                      last_status INTEGER,
                      hit_count INTEGER DEFAULT 0,
                      updated_at TEXT
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS http_failures (
                      url TEXT PRIMARY KEY,
                      last_error TEXT,
                      count INTEGER DEFAULT 0,
                      last_at TEXT
                    )
                    """
                )

    def get_conditional_headers(self, url: str) -> Dict[str, str]:
        with closing(sqlite3.connect(self.path)) as conn:
            cur = conn.execute("SELECT etag, last_modified FROM http_cache WHERE url = ?", (url,))
            row = cur.fetchone()
            headers: Dict[str, str] = {}
            if row:
                etag, last_mod = row
                if etag:
                    headers["If-None-Match"] = etag
                if last_mod:
                    headers["If-Modified-Since"] = last_mod
            return headers

    def update_from_response(self, url: str, resp) -> None:
        etag = resp.headers.get("ETag")
        last_mod = resp.headers.get("Last-Modified")
        status = int(getattr(resp, "status_code", 0) or 0)
        now = datetime.utcnow().isoformat()
        with closing(sqlite3.connect(self.path)) as conn:
            with conn:
                conn.execute(
                    """
                    INSERT INTO http_cache(url, etag, last_modified, last_status, hit_count, updated_at)
                    VALUES(?,?,?,?,1,?)
                    ON CONFLICT(url) DO UPDATE SET
                      etag=COALESCE(excluded.etag, http_cache.etag),
                      last_modified=COALESCE(excluded.last_modified, http_cache.last_modified),
                      last_status=excluded.last_status,
                      hit_count=http_cache.hit_count + 1,
                      updated_at=excluded.updated_at
                    """,
                    (url, etag, last_mod, status, now),
                )

    def record_failure(self, url: str, error: str) -> None:
        now = datetime.utcnow().isoformat()
        with closing(sqlite3.connect(self.path)) as conn:
            with conn:
                conn.execute(
                    """
                    INSERT INTO http_failures(url, last_error, count, last_at)
                    VALUES(?,?,1,?)
                    ON CONFLICT(url) DO UPDATE SET
                      last_error=excluded.last_error,
                      count=http_failures.count + 1,
                      last_at=excluded.last_at
                    """,
                    (url, error, now),
                )

    def failure_report(self) -> Dict[str, Dict[str, object]]:
        with closing(sqlite3.connect(self.path)) as conn:
            cur = conn.execute("SELECT url, last_error, count, last_at FROM http_failures ORDER BY count DESC, last_at DESC")
            out: Dict[str, Dict[str, object]] = {}
            for url, err, cnt, at in cur.fetchall():
                out[url] = {"error": err, "count": cnt, "lastAt": at}
            return out

