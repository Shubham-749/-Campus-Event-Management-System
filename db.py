"""SQLite data access: schema, seed data, and query/update functions."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "var" / "campus_events.db"

HOLDING_STATUSES = ("PENDING", "CONFIRMED", "BLOCKED")

SCHEMA = """
CREATE TABLE IF NOT EXISTS venues (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL,
    capacity INTEGER NOT NULL CHECK (capacity > 0)
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    event_type TEXT NOT NULL,
    venue_id INTEGER NOT NULL REFERENCES venues(id),
    start_at TEXT NOT NULL,
    end_at TEXT NOT NULL,
    attendance INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL CHECK (status IN ('PENDING','CONFIRMED','REJECTED','CANCELLED','BLOCKED')),
    reason TEXT
);
CREATE INDEX IF NOT EXISTS idx_events_venue_time ON events (venue_id, start_at, end_at);
"""

SEED_VENUES = [
    ("Seminar Hall A", "Seminar Hall", 120),
    ("Main Auditorium", "Auditorium", 500),
    ("Conference Room C", "Conference Room", 40),
    ("Central Amphitheatre", "Open Venue", 300),
    ("Innovation Lab", "Computer Lab", 60),
]

SEED_EVENTS = [
    ("Department Seminar", "Seminar", "Seminar Hall A", "2026-08-04T10:00", "2026-08-04T12:00", 100, "CONFIRMED", None),
    ("Coding Workshop", "Workshop", "Innovation Lab", "2026-08-06T14:00", "2026-08-06T17:00", 50, "CONFIRMED", None),
    ("Renovation", "Maintenance", "Conference Room C", "2026-08-04T09:00", "2026-08-04T18:00", 0, "BLOCKED", "Renovation"),
]


def _connect() -> sqlite3.Connection:
    """Open a fresh connection per call; rows come back as dict-like Row objects."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(reset: bool = False) -> None:
    """Create the schema and seed the brief's venues, confirmed events and renovation block on first run."""
    if reset and DB_PATH.exists():
        DB_PATH.unlink()
    conn = _connect()
    try:
        with conn:
            conn.executescript(SCHEMA)
            if conn.execute("SELECT COUNT(*) FROM venues").fetchone()[0] == 0:
                conn.executemany("INSERT INTO venues (name, type, capacity) VALUES (?, ?, ?)", SEED_VENUES)
                ids = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM venues")}
                conn.executemany(
                    "INSERT INTO events (title, event_type, venue_id, start_at, end_at, attendance, status, reason)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    [(t, et, ids[v], s, e, a, st, r) for t, et, v, s, e, a, st, r in SEED_EVENTS],
                )
    finally:
        conn.close()


def list_venues() -> list[dict]:
    """Return all venues ordered by name."""
    conn = _connect()
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM venues ORDER BY name")]
    finally:
        conn.close()


def get_venue(venue_id: int) -> dict | None:
    """Return one venue, or None if it doesn't exist."""
    conn = _connect()
    try:
        row = conn.execute("SELECT * FROM venues WHERE id = ?", (venue_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


_EVENT_SELECT = (
    "SELECT e.*, v.name AS venue_name FROM events e JOIN venues v ON v.id = e.venue_id"
)


def list_events(venue_id: int | None = None) -> list[dict]:
    """Return all events and blocks (any status), optionally for one venue, ordered by start time."""
    conn = _connect()
    try:
        if venue_id is None:
            rows = conn.execute(_EVENT_SELECT + " ORDER BY e.start_at, e.id")
        else:
            rows = conn.execute(_EVENT_SELECT + " WHERE e.venue_id = ? ORDER BY e.start_at, e.id", (venue_id,))
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_event(event_id: int) -> dict | None:
    """Return one event, or None if it doesn't exist."""
    conn = _connect()
    try:
        row = conn.execute(_EVENT_SELECT + " WHERE e.id = ?", (event_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def find_overlaps(venue_id: int, start: str, end: str, exclude_id: int | None = None) -> list[dict]:
    """Return holding rows (PENDING/CONFIRMED/BLOCKED) on the venue overlapping the half-open [start, end)."""
    conn = _connect()
    try:
        rows = conn.execute(
            _EVENT_SELECT + " WHERE e.venue_id = ? AND e.status IN (?, ?, ?)"
            " AND e.start_at < ? AND ? < e.end_at AND e.id IS NOT ?"
            " ORDER BY e.start_at, e.id",
            (venue_id, *HOLDING_STATUSES, end, start, exclude_id),
        )
        return [dict(r) for r in rows]
    finally:
        conn.close()


def insert_event(title: str, event_type: str, venue_id: int, start: str, end: str, attendance: int, status: str) -> int:
    """Insert an event row and return its id."""
    conn = _connect()
    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO events (title, event_type, venue_id, start_at, end_at, attendance, status)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (title, event_type, venue_id, start, end, attendance, status),
            )
        return cur.lastrowid
    finally:
        conn.close()


def update_status(event_id: int, status: str, reason: str | None = None) -> None:
    """Set an event's status and reason; releasing the venue follows from the status alone."""
    conn = _connect()
    try:
        with conn:
            conn.execute("UPDATE events SET status = ?, reason = ? WHERE id = ?", (status, reason, event_id))
    finally:
        conn.close()
