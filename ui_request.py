"""Requester screens: event request form (MVP-2) and schedule table (MVP-3)."""

from datetime import date, datetime, time

import streamlit as st

import db

try:
    import workflow
except ImportError:
    workflow = None

ALL_VENUES = "All venues"
STATUS_LABELS = {
    "PENDING": "Pending",
    "CONFIRMED": "Confirmed",
    "REJECTED": "Rejected",
    "CANCELLED": "Cancelled",
    "BLOCKED": "Blocked",
}


def _iso(d: date, t: time) -> str:
    """Combine a date and time into the shared ISO format YYYY-MM-DDTHH:MM."""
    return datetime.combine(d, t).strftime("%Y-%m-%dT%H:%M")


def _display(iso: str) -> str:
    """Format an ISO date-time for the schedule table."""
    return datetime.strptime(iso, "%Y-%m-%dT%H:%M").strftime("%d %b %Y %H:%M")


def render_request_form() -> None:
    """Collect a request and show success or every refusal reason together (MVP-2)."""
    st.header("Request an event")
    if "last_submitted" in st.session_state:
        st.success(f"Request #{st.session_state.pop('last_submitted')} submitted and is now Pending.")

    venues = db.list_venues()
    with st.form("request_form", clear_on_submit=False):
        title = st.text_input("Title")
        event_type = st.text_input("Event type", placeholder="e.g. Seminar, Workshop, Hackathon")
        venue = st.selectbox(
            "Venue",
            venues,
            format_func=lambda v: f"{v['name']} ({v['type']}, capacity {v['capacity']})",
        )
        col_start, col_end = st.columns(2)
        with col_start:
            start_date = st.date_input("Start date")
            start_time = st.time_input("Start time", value=time(10, 0))
        with col_end:
            end_date = st.date_input("End date")
            end_time = st.time_input("End time", value=time(12, 0))
        attendance = st.number_input("Expected attendance", min_value=0, step=1, value=0)
        submitted = st.form_submit_button("Submit request")

    if not submitted:
        return
    if not title.strip() or not event_type.strip():
        st.error("Title and event type are required.")
        return
    if workflow is None:
        st.error("Request submission isn't available yet (workflow.py not merged).")
        return

    form = {
        "title": title.strip(),
        "event_type": event_type.strip(),
        "venue_id": venue["id"],
        "start": _iso(start_date, start_time),
        "end": _iso(end_date, end_time),
        "attendance": int(attendance),
    }
    ok, reasons, event_id = workflow.submit_request(form)
    if ok:
        st.session_state["last_submitted"] = event_id
        st.rerun()
    st.error("Request refused:\n\n" + "\n".join(f"- {r}" for r in reasons))


def render_schedule() -> None:
    """Show every event and block with venue, time and status, filterable by venue (MVP-3)."""
    st.header("Schedule")
    venues = db.list_venues()
    choice = st.selectbox(
        "Venue filter",
        [None, *venues],
        format_func=lambda v: ALL_VENUES if v is None else v["name"],
    )
    events = db.list_events(None if choice is None else choice["id"])
    if not events:
        st.info("No events for this venue.")
        return
    st.dataframe(
        [
            {
                "ID": e["id"],
                "Title": e["title"],
                "Type": e["event_type"],
                "Venue": e["venue_name"],
                "Start": _display(e["start_at"]),
                "End": _display(e["end_at"]),
                "Attendance": e["attendance"],
                "Status": STATUS_LABELS.get(e["status"], e["status"]),
                "Reason": e["reason"] or "",
            }
            for e in events
        ],
        hide_index=True,
    )
