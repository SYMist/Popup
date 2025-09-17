from __future__ import annotations

import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime
from typing import Any, Dict, Iterable

import orjson


DATA_DIR = os.path.join("data", "popups")
DB_PATH = os.path.join("data", "popups.sqlite")


def ensure_dirs() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs("data", exist_ok=True)


def dump_json(path: str, data: Dict[str, Any]) -> None:
    with open(path, "wb") as f:
        f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS))


def save_record_json(record: Dict[str, Any]) -> str:
    ensure_dirs()
    rid = record["id"]
    path = os.path.join(DATA_DIR, f"{rid}.json")
    dump_json(path, record)
    return path


def init_db(conn: sqlite3.Connection) -> None:
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS popups (
              id TEXT PRIMARY KEY,
              category TEXT,
              startDate TEXT,
              endDate TEXT,
              lon REAL,
              lat REAL,
              city TEXT,
              priceType TEXT,
              createdAt TEXT,
              updatedAt TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS popup_translations (
              popupId TEXT,
              locale TEXT,
              title TEXT,
              address TEXT,
              priceDesc TEXT,
              PRIMARY KEY (popupId, locale)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS popup_images (
              popupId TEXT,
              url TEXT,
              variant TEXT,
              "order" INTEGER,
              role TEXT,
              PRIMARY KEY (popupId, url)
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_popups_end ON popups(endDate)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_popups_cat_start ON popups(category, startDate)")


def upsert_records_sqlite(records: Iterable[Dict[str, Any]]) -> str:
    ensure_dirs()
    with closing(sqlite3.connect(DB_PATH)) as conn:
        init_db(conn)
        now = datetime.utcnow().isoformat()
        with conn:
            for r in records:
                start = r.get("duration", {}).get("start")
                end = r.get("duration", {}).get("end")
                lon = r.get("geo", {}).get("lon")
                lat = r.get("geo", {}).get("lat")
                city = r.get("address", {}).get("city")
                price_type = r.get("pricing", {}).get("type")
                conn.execute(
                    """
                    INSERT INTO popups(id, category, startDate, endDate, lon, lat, city, priceType, createdAt, updatedAt)
                    VALUES(?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(id) DO UPDATE SET
                      category=excluded.category,
                      startDate=excluded.startDate,
                      endDate=excluded.endDate,
                      lon=excluded.lon,
                      lat=excluded.lat,
                      city=excluded.city,
                      priceType=excluded.priceType,
                      updatedAt=excluded.updatedAt
                    """,
                    (
                        r["id"],
                        r.get("category"),
                        start,
                        end,
                        lon,
                        lat,
                        city,
                        price_type,
                        now,
                        now,
                    ),
                )
                # translations
                tr = r.get("translations", {})
                for loc in ("ko", "en", "ja", "zh-cn", "zh-CN"):
                    t = tr.get(loc, {}) if isinstance(tr, dict) else {}
                    conn.execute(
                        """
                        INSERT INTO popup_translations(popupId, locale, title, address, priceDesc)
                        VALUES(?,?,?,?,?)
                        ON CONFLICT(popupId, locale) DO UPDATE SET
                          title=excluded.title,
                          address=excluded.address,
                          priceDesc=excluded.priceDesc
                        """,
                        (
                            r["id"],
                            loc,
                            t.get("title"),
                            t.get("address"),
                            t.get("priceDesc"),
                        ),
                    )
                # images
                conn.execute("DELETE FROM popup_images WHERE popupId = ?", (r["id"],))
                for idx, img in enumerate(r.get("images", [])):
                    conn.execute(
                        """
                        INSERT INTO popup_images(popupId, url, variant, "order", role)
                        VALUES(?,?,?,?,?)
                        """,
                        (r["id"], img.get("url"), img.get("variant"), idx, img.get("role")),
                    )
    return DB_PATH
