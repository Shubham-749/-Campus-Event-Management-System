"""Event use cases: validate requests and enforce review and cancellation rules."""

import db
import notifications
import rules


def submit_request(form: dict) -> tuple[bool, list[str], int | None]:
    """Save a valid request as PENDING, holding its venue until a decision."""
    venue = db.get_venue(form.get("venue_id"))
    start, end = form.get("start"), form.get("end")
    attendance = form.get("attendance")
    conflicts = []
    try:
        start = rules.normalize_time(start)
        end = rules.normalize_time(end)
    except (TypeError, ValueError):
        pass
    else:
        if venue and start < end:
            conflicts = db.find_overlaps(venue["id"], start, end)

    reasons = rules.validate_request(venue, start, end, attendance, conflicts)
    if reasons:
        return False, reasons, None

    event_id = db.insert_event(
        form["title"], form["event_type"], venue["id"],
        start, end, attendance, "PENDING",
    )
    return True, [], event_id


def approve(event_id: int) -> tuple[bool, list[str]]:
    """Confirm only a PENDING request after rechecking other venue holds."""
    event = db.get_event(event_id)
    if event is None:
        return False, [f"Event {event_id} does not exist"]

    reasons = rules.validate_transition(event["status"], "approve")
    if reasons:
        return False, reasons

    venue = db.get_venue(event["venue_id"])
    conflicts = db.find_overlaps(
        event["venue_id"], event["start_at"], event["end_at"],
        exclude_id=event_id,
    )
    reasons = rules.validate_request(
        venue, event["start_at"], event["end_at"], event["attendance"], conflicts,
    )
    if reasons:
        return False, reasons

    db.update_status(event_id, "CONFIRMED")
    _notify_decision(event, "CONFIRMED")
    return True, []


def _notify_decision(event: dict, status: str, reason: str | None = None) -> None:
    """Tell the requester about a decision on their request (BONUS-1)."""
    message = f"'{event['title']}' at {event['venue_name']} is now {status}"
    notifications.notify(event["id"], f"{message}: {reason}" if reason else message)


def _close_event(event_id: int, action: str, reason: str) -> tuple[bool, list[str]]:
    """Require an allowed transition and a reason before releasing a venue."""
    event = db.get_event(event_id)
    if event is None:
        return False, [f"Event {event_id} does not exist"]

    reasons = rules.validate_transition(event["status"], action, reason)
    if reasons:
        return False, reasons

    status = rules.next_status(event["status"], action)
    db.update_status(event_id, status, reason.strip())
    _notify_decision(event, status, reason.strip())
    return True, []


def reject(event_id: int, reason: str) -> tuple[bool, list[str]]:
    """Reject only a PENDING request with a reason and immediately release its venue."""
    return _close_event(event_id, "reject", reason)


def cancel(event_id: int, reason: str) -> tuple[bool, list[str]]:
    """Cancel only a CONFIRMED event with a reason and immediately release its venue."""
    return _close_event(event_id, "cancel", reason)
