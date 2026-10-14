"""Tests for rules.py: overlap, request validation and status transitions (MVP-6)."""

import pytest

import rules

SEMINAR_HALL = {"id": 1, "name": "Seminar Hall A", "type": "Seminar Hall", "capacity": 120}
INNOVATION_LAB = {"id": 5, "name": "Innovation Lab", "type": "Computer Lab", "capacity": 60}
SEMINAR_EVENT = {
    "title": "Department Seminar", "status": "CONFIRMED", "venue_name": "Seminar Hall A",
    "start_at": "2026-08-04T10:00", "end_at": "2026-08-04T12:00", "reason": None,
}
RENOVATION = {
    "title": "Renovation", "status": "BLOCKED", "venue_name": "Conference Room C",
    "start_at": "2026-08-04T09:00", "end_at": "2026-08-04T18:00", "reason": "Renovation",
}


# --- overlaps -----------------------------------------------------------------

@pytest.mark.parametrize("start, end", [
    ("2026-08-04T11:00", "2026-08-04T13:00"),  # partial overlap at the end
    ("2026-08-04T09:00", "2026-08-04T11:00"),  # partial overlap at the start
    ("2026-08-04T09:00", "2026-08-04T13:00"),  # fully contains existing
    ("2026-08-04T10:30", "2026-08-04T11:00"),  # inside existing
    ("2026-08-04T10:00", "2026-08-04T12:00"),  # identical
])
def test_overlapping_intervals_conflict(start, end):
    assert rules.overlaps(start, end, "2026-08-04T10:00", "2026-08-04T12:00")


@pytest.mark.parametrize("start, end", [
    ("2026-08-04T12:00", "2026-08-04T13:00"),  # starts exactly when existing ends
    ("2026-08-04T08:00", "2026-08-04T10:00"),  # ends exactly when existing starts
    ("2026-08-05T10:00", "2026-08-05T12:00"),  # different day
])
def test_non_overlapping_intervals_do_not_conflict(start, end):
    assert not rules.overlaps(start, end, "2026-08-04T10:00", "2026-08-04T12:00")


def test_overlap_ignores_seconds_and_format_differences():
    assert not rules.overlaps("2026-08-04T12:00:00", "2026-08-04T13:00", "2026-08-04T10:00", "2026-08-04T12:00")


def test_overnight_event_overlaps_next_morning():
    assert rules.overlaps("2026-08-10T18:00", "2026-08-11T06:00", "2026-08-11T05:00", "2026-08-11T07:00")


# --- validate_request ---------------------------------------------------------

def test_valid_request_has_no_reasons():
    assert rules.validate_request(SEMINAR_HALL, "2026-08-04T12:00", "2026-08-04T13:00", 100, [SEMINAR_EVENT]) == []


def test_conflict_with_confirmed_event_is_explained():
    reasons = rules.validate_request(SEMINAR_HALL, "2026-08-04T11:00", "2026-08-04T13:00", 100, [SEMINAR_EVENT])
    assert reasons == ["Conflicts with CONFIRMED event 'Department Seminar' on 2026-08-04 10:00–12:00"]


def test_conflict_with_pending_request_blocks():
    pending = {**SEMINAR_EVENT, "status": "PENDING", "title": "Club Meetup"}
    reasons = rules.validate_request(SEMINAR_HALL, "2026-08-04T11:00", "2026-08-04T13:00", 50, [pending])
    assert reasons == ["Conflicts with PENDING event 'Club Meetup' on 2026-08-04 10:00–12:00"]


def test_block_is_explained_with_its_reason():
    room = {"id": 3, "name": "Conference Room C", "type": "Conference Room", "capacity": 40}
    reasons = rules.validate_request(room, "2026-08-04T14:00", "2026-08-04T15:00", 20, [RENOVATION])
    assert reasons == ["Conference Room C is unavailable (Renovation) on 2026-08-04 09:00–18:00"]


@pytest.mark.parametrize("status", ["REJECTED", "CANCELLED"])
def test_released_events_do_not_block(status):
    released = {**SEMINAR_EVENT, "status": status}
    assert rules.validate_request(SEMINAR_HALL, "2026-08-04T11:00", "2026-08-04T13:00", 100, [released]) == []


def test_capacity_exceeded_is_refused():
    reasons = rules.validate_request(INNOVATION_LAB, "2026-08-10T10:00", "2026-08-10T12:00", 80, [])
    assert reasons == ["Expected attendance 80 exceeds Innovation Lab capacity of 60"]


def test_attendance_equal_to_capacity_is_allowed():
    assert rules.validate_request(SEMINAR_HALL, "2026-08-10T10:00", "2026-08-10T12:00", 120, []) == []


@pytest.mark.parametrize("attendance", [0, -5, 2.5, "50", None, True])
def test_invalid_attendance_is_refused(attendance):
    reasons = rules.validate_request(SEMINAR_HALL, "2026-08-10T10:00", "2026-08-10T12:00", attendance, [])
    assert reasons == ["Expected attendance must be a whole number greater than 0"]


@pytest.mark.parametrize("start, end", [
    ("2026-08-10T12:00", "2026-08-10T10:00"),  # end before start
    ("2026-08-10T10:00", "2026-08-10T10:00"),  # zero length
])
def test_end_must_be_after_start(start, end):
    assert rules.validate_request(SEMINAR_HALL, start, end, 50, []) == ["End time must be after start time"]


def test_unparseable_time_is_refused():
    reasons = rules.validate_request(SEMINAR_HALL, "not-a-date", "2026-08-10T10:00", 50, [])
    assert reasons == ["Start and end must be valid date-times (YYYY-MM-DDTHH:MM)"]


def test_missing_venue_is_refused():
    assert rules.validate_request(None, "2026-08-10T10:00", "2026-08-10T12:00", 50, []) == ["Please select a venue"]


def test_multi_day_event_is_allowed():
    assert rules.validate_request(SEMINAR_HALL, "2026-08-10T18:00", "2026-08-11T06:00", 100, []) == []


def test_all_reasons_are_returned_together():
    reasons = rules.validate_request(INNOVATION_LAB, "2026-08-10T12:00", "2026-08-10T10:00", 80, [])
    assert reasons == [
        "End time must be after start time",
        "Expected attendance 80 exceeds Innovation Lab capacity of 60",
    ]


# --- transitions --------------------------------------------------------------

@pytest.mark.parametrize("from_status, action, target", [
    ("PENDING", "approve", "CONFIRMED"),
    ("PENDING", "reject", "REJECTED"),
    ("CONFIRMED", "cancel", "CANCELLED"),
])
def test_allowed_transitions(from_status, action, target):
    assert rules.can_transition(from_status, action)
    assert rules.next_status(from_status, action) == target


@pytest.mark.parametrize("from_status, action", [
    ("CONFIRMED", "approve"),
    ("REJECTED", "approve"),
    ("CANCELLED", "cancel"),
    ("PENDING", "cancel"),
    ("REJECTED", "reject"),
    ("BLOCKED", "approve"),
])
def test_forbidden_transitions(from_status, action):
    assert not rules.can_transition(from_status, action)
    assert rules.next_status(from_status, action) is None


@pytest.mark.parametrize("action", ["reject", "cancel"])
def test_reject_and_cancel_require_a_reason(action):
    from_status = "PENDING" if action == "reject" else "CONFIRMED"
    assert rules.validate_transition(from_status, action, "  ") == [f"A reason is required to {action}"]
    assert rules.validate_transition(from_status, action, "Venue needed for exams") == []


def test_invalid_transition_is_explained():
    assert rules.validate_transition("CANCELLED", "approve") == ["Cannot approve an event that is CANCELLED"]


def test_normalize_time_produces_storage_format():
    assert rules.normalize_time("2026-08-04T10:00:45") == "2026-08-04T10:00"
