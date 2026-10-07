"""
PyShort - Database Access Layer
Provides clean, safe, and parameterized SQLite interactions for PyShort.
"""

import os
import sqlite3
from datetime import datetime, timezone

# Resolve database file path relative to this file's directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")


def get_db_path(db_path=None):
    """Dynamically resolve database path, checking environment overrides."""
    if db_path:
        return db_path
    return os.environ.get("PYSHORT_DB_PATH", os.path.join(BASE_DIR, "pyshort.db"))


def get_db(db_path=None):
    """
    Establish a connection to the SQLite database.
    Enables foreign keys and returns rows accessible by column name.
    """
    target_path = get_db_path(db_path)
    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path=None):
    """
    Initializes the database schema if tables do not exist.
    """
    target_path = get_db_path(db_path)
    with get_db(target_path) as conn:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()


def code_exists(short_code, db_path=None):
    """
    Checks if a short code already exists in the database.
    Case-insensitive check due to SQLite COLLATE NOCASE.
    """
    with get_db(db_path) as conn:
        cursor = conn.execute(
            "SELECT 1 FROM urls WHERE short_code = ? LIMIT 1",
            (short_code.strip(),)
        )
        return cursor.fetchone() is not None


def get_url_by_code(short_code, db_path=None):
    """
    Fetch URL entry by short code.
    Returns a dict or None.
    """
    with get_db(db_path) as conn:
        cursor = conn.execute(
            "SELECT id, original_url, short_code, is_custom, clicks, created_at, last_clicked_at "
            "FROM urls WHERE short_code = ?",
            (short_code.strip(),)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_url_by_id(url_id, db_path=None):
    """
    Fetch URL entry by primary key ID.
    """
    with get_db(db_path) as conn:
        cursor = conn.execute(
            "SELECT id, original_url, short_code, is_custom, clicks, created_at, last_clicked_at "
            "FROM urls WHERE id = ?",
            (url_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_url_by_original(original_url, db_path=None):
    """
    Find existing non-custom shortened URL for identical long URL if available.
    """
    with get_db(db_path) as conn:
        cursor = conn.execute(
            "SELECT id, original_url, short_code, is_custom, clicks, created_at, last_clicked_at "
            "FROM urls WHERE original_url = ? AND is_custom = 0 "
            "ORDER BY id DESC LIMIT 1",
            (original_url.strip(),)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def create_url(original_url, short_code, is_custom=False, db_path=None):
    """
    Insert a newly shortened URL into the database.
    Returns the created URL dictionary.
    """
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO urls (original_url, short_code, is_custom, clicks, created_at)
            VALUES (?, ?, ?, 0, CURRENT_TIMESTAMP)
            """,
            (original_url.strip(), short_code.strip(), 1 if is_custom else 0)
        )
        url_id = cursor.lastrowid
        conn.commit()

    return get_url_by_id(url_id, db_path=db_path)


def record_click(short_code, user_agent=None, referrer=None, db_path=None):
    """
    Atomically increments click count for a short code and logs the click audit event.
    Returns the updated URL dictionary, or None if code not found.
    """
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM urls WHERE short_code = ?",
            (short_code.strip(),)
        )
        row = cursor.fetchone()
        if not row:
            return None

        url_id = row["id"]
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            """
            UPDATE urls 
            SET clicks = clicks + 1, last_clicked_at = ?
            WHERE id = ?
            """,
            (now, url_id)
        )

        cursor.execute(
            """
            INSERT INTO click_logs (url_id, clicked_at, user_agent, referrer)
            VALUES (?, ?, ?, ?)
            """,
            (url_id, now, (user_agent or "")[:255], (referrer or "")[:255])
        )
        conn.commit()

    return get_url_by_id(url_id, db_path=db_path)


def get_recent_urls(limit=20, db_path=None):
    """
    Returns a list of recently shortened URLs ordered by creation date descending.
    """
    with get_db(db_path) as conn:
        cursor = conn.execute(
            """
            SELECT id, original_url, short_code, is_custom, clicks, created_at, last_clicked_at
            FROM urls
            ORDER BY id DESC
            LIMIT ?
            """,
            (max(1, int(limit)),)
        )
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def get_analytics_summary(db_path=None):
    """
    Calculates summary metrics:
    - total_urls
    - total_clicks
    - avg_clicks_per_url
    - most_active_url (top clicked URL)
    """
    with get_db(db_path) as conn:
        # Total counts
        stats_cursor = conn.execute(
            """
            SELECT 
                COUNT(*) AS total_urls,
                COALESCE(SUM(clicks), 0) AS total_clicks
            FROM urls
            """
        )
        stats = dict(stats_cursor.fetchone() or {"total_urls": 0, "total_clicks": 0})

        # Most active link
        top_cursor = conn.execute(
            """
            SELECT id, original_url, short_code, clicks, created_at
            FROM urls
            WHERE clicks > 0
            ORDER BY clicks DESC, id DESC
            LIMIT 1
            """
        )
        top_row = top_cursor.fetchone()
        stats["most_active"] = dict(top_row) if top_row else None

        total_urls = stats["total_urls"]
        total_clicks = stats["total_clicks"]
        stats["avg_clicks"] = round(total_clicks / total_urls, 1) if total_urls > 0 else 0.0

        return stats


def delete_url(url_id, db_path=None):
    """
    Deletes a shortened URL and its associated click logs (cascade).
    Returns True if deleted, False otherwise.
    """
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM urls WHERE id = ?", (int(url_id),))
        conn.commit()
        return cursor.rowcount > 0
