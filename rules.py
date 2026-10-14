"""Pure business rules: overlap, request validation and status transitions. No I/O, no project imports."""

from datetime import datetime

# Mirrors db.HOLDING_STATUSES; rules.py stays import-free by design (AGENTS.md §2.5).
HOLDING_STATUSES = ("PENDING", "CONFIRMED", "BLOCKED")

TRANSITIONS = {
    ("PENDING", "approve"): "CONFIRMED",
    ("PENDING", "reject"): "REJECTED",
    ("CONFIRMED", "cancel"): "CANCELLED",
}
REASON_REQUIRED = {"reject", "cancel"}

TIME_FORMAT = "%Y-%m-%dT%H:%M"


def parse_time(value: str | datetime) -> datetime:
    """Parse an ISO date-time (string or datetime) and truncate to minute precision."""
    dt = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
    return dt.replace(second=0, microsecond=0, tzinfo=None)


def normalize_time(value: str | datetime) -> str:
    """Return the canonical storage format YYYY-MM-DDTHH:MM."""
    return parse_time(value).strftime(TIME_FORMAT)


def overlaps(a_start: str | datetime, a_end: str | datetime, b_start: str | datetime, b_end: str | datetime) -> bool:
    """Half-open interval overlap: back-to-back slots (one ends when the other starts) do not conflict."""
    return parse_time(a_start) < parse_time(b_end) and parse_time(b_start) < parse_time(a_end)


def format_interval(start: str | datetime, end: str | datetime) -> str:
    """Human-readable interval, e.g. '2026-08-04 10:00–12:00' or across days '2026-08-04 18:00 – 2026-08-05 06:00'."""
    s, e = parse_time(start), parse_time(end)
    if s.date() == e.date():
        return f"{s:%Y-%m-%d %H:%M}–{e:%H:%M}"
    return f"{s:%Y-%m-%d %H:%M} – {e:%Y-%m-%d %H:%M}"


def _conflict_message(row: dict, venue_name: str) -> str:
    """Explain why an existing holding row blocks the request."""
    interval = format_interval(row["start_at"], row["end_at"])
    if row["status"] == "BLOCKED":
        cause = row.get("reason") or row.get("title") or "Maintenance"
        return f"{row.get('venue_name') or venue_name} is unavailable ({cause}) on {interval}"
    return f"Conflicts with {row['status']} event '{row.get('title', '')}' on {interval}"


def validate_request(venue: dict | None, start, end, attendance, conflicts: list[dict] | None) -> list[str]:
    """Return every reason the request cannot proceed (BC 1, 2, 3, 4, 10); an empty list means valid."""
    reasons: list[str] = []

    if not venue:
        reasons.append("Please select a venue")

    times_ok = True
    try:
        s, e = parse_time(start), parse_time(end)
    except (TypeError, ValueError):
        times_ok = False
        reasons.append("Start and end must be valid date-times (YYYY-MM-DDTHH:MM)")
    else:
        if e <= s:
            times_ok = False
            reasons.append("End time must be after start time")

    attendance_ok = isinstance(attendance, int) and not isinstance(attendance, bool) and attendance > 0
    if not attendance_ok:
        reasons.append("Expected attendance must be a whole number greater than 0")
    elif venue and attendance > venue["capacity"]:
        reasons.append(f"Expected attendance {attendance} exceeds {venue['name']} capacity of {venue['capacity']}")

    if venue and times_ok:
        for row in conflicts or []:
            if row["status"] in HOLDING_STATUSES and overlaps(s, e, row["start_at"], row["end_at"]):
                reasons.append(_conflict_message(row, venue["name"]))

    return reasons


def can_transition(from_status: str, action: str) -> bool:
    """True if the action is allowed from the current status (approve/reject from PENDING, cancel from CONFIRMED)."""
    return (from_status, action) in TRANSITIONS


def next_status(from_status: str, action: str) -> str | None:
    """Target status for an allowed transition, or None if it isn't allowed."""
    return TRANSITIONS.get((from_status, action))


def validate_transition(from_status: str, action: str, reason: str | None = None) -> list[str]:
    """Return reasons a status change is refused (BC 5, 6, 7); reject and cancel require a reason."""
    reasons: list[str] = []
    if not can_transition(from_status, action):
        reasons.append(f"Cannot {action} an event that is {from_status}")
    if action in REASON_REQUIRED and not (reason and reason.strip()):
        reasons.append(f"A reason is required to {action}")
    return reasons
