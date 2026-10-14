"""BONUS-1: in-app notifications for request decisions, stored in their own table."""

import sqlite3
from datetime import datetime

import db

SCHEMA = """
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY,
    event_id INTEGER NOT NULL REFERENCES events(id),
    message TEXT NOT NULL,
    is_read INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
"""


def _connect() -> sqlite3.Connection:
    """Open a fresh connection to the shared DB file and ensure the notifications table exists."""
    db.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def notify(event_id: int, message: str) -> None:
    """Record a decision notification for the requester (approve, reject or cancel)."""
    conn = _connect()
    try:
        with conn:
            conn.execute(
                "INSERT INTO notifications (event_id, message, created_at) VALUES (?, ?, ?)",
                (event_id, message, datetime.now().strftime("%Y-%m-%dT%H:%M:%S")),
            )
    finally:
        conn.close()


def list_notifications() -> list[dict]:
    """Return all notifications, newest first."""
    conn = _connect()
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM notifications ORDER BY id DESC")]
    finally:
        conn.close()


def mark_all_read() -> None:
    """Mark every notification as read, clearing the unread count."""
    conn = _connect()
    try:
        with conn:
            conn.execute("UPDATE notifications SET is_read = 1 WHERE is_read = 0")
    finally:
        conn.close()
