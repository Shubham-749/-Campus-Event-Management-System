"""Reviewer screens: pending approvals and confirmed-event cancellation."""

from datetime import datetime

import streamlit as st

import db
import workflow

STATUS_LABELS = {
    "PENDING": "Pending",
    "CONFIRMED": "Confirmed",
}


def _display(iso: str) -> str:
    """Format an ISO date-time for reviewer screens."""
    return datetime.strptime(iso, "%Y-%m-%dT%H:%M").strftime("%d %b %Y %H:%M")


def _event_summary(event: dict) -> str:
    """Format the event details shown in an action panel."""
    return (
        f"{event['title']} | {event['venue_name']} | "
        f"{_display(event['start_at'])} - {_display(event['end_at'])} | "
        f"{event['attendance']} attendees"
    )


def render_review_queue() -> None:
    """Show pending requests with approve and reasoned reject actions."""
    st.header("Review queue")
    pending = [event for event in db.list_events() if event["status"] == "PENDING"]
    if not pending:
        st.info("There are no pending requests.")
        return

    for event in pending:
        with st.expander(_event_summary(event), expanded=True):
            st.write(f"**Event type:** {event['event_type']}")
            st.write(f"**Venue capacity:** {event['attendance']} / {db.get_venue(event['venue_id'])['capacity']}")
            approve_key = f"approve_{event['id']}"
            if st.button("Approve", key=approve_key):
                ok, reasons = workflow.approve(event["id"])
                if ok:
                    st.success("Request approved.")
                    st.rerun()
                for reason in reasons:
                    st.error(reason)

            with st.form(f"reject_form_{event['id']}"):
                reason = st.text_area("Rejection reason", key=f"reject_reason_{event['id']}")
                submitted = st.form_submit_button("Reject request")
            if submitted:
                ok, reasons = workflow.reject(event["id"], reason)
                if ok:
                    st.success("Request rejected and the venue hold was released.")
                    st.rerun()
                for refusal in reasons:
                    st.error(refusal)


def render_cancel_panel() -> None:
    """Show confirmed events with a required cancellation reason."""
    st.header("Cancel confirmed events")
    confirmed = [event for event in db.list_events() if event["status"] == "CONFIRMED"]
    if not confirmed:
        st.info("There are no confirmed events to cancel.")
        return

    for event in confirmed:
        with st.expander(_event_summary(event)):
            with st.form(f"cancel_form_{event['id']}"):
                reason = st.text_area("Cancellation reason", key=f"cancel_reason_{event['id']}")
                submitted = st.form_submit_button("Cancel event")
            if submitted:
                ok, reasons = workflow.cancel(event["id"], reason)
                if ok:
                    st.success("Event cancelled and the venue was released.")
                    st.rerun()
                for refusal in reasons:
                    st.error(refusal)
