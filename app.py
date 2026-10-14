"""Streamlit shell: page setup, sidebar role switcher, reset button, layout."""

import streamlit as st

import db
import ui_request

try:
    import ui_review
except ImportError:
    ui_review = None

ROLES = ("Requester", "Reviewer")


def render_sidebar() -> str:
    """Show the role switcher and demo reset; return the selected role (MVP-1)."""
    st.sidebar.title("Campus Events")
    role = st.sidebar.radio("Role", ROLES)
    st.sidebar.divider()
    if st.sidebar.button("Reset demo data"):
        db.init_db(reset=True)
        st.rerun()
    return role


def render_reviewer() -> None:
    """Show the reviewer screens owned by P5, or a placeholder until they're merged."""
    if ui_review is None:
        st.info("Reviewer screens aren't available yet (ui_review.py not merged).")
        return
    ui_review.render_review_queue()
    ui_review.render_cancel_panel()


def main() -> None:
    """Seed the database on first run and route to the selected role's screens."""
    st.set_page_config(page_title="Campus Event Management", layout="wide")
    db.init_db()
    role = render_sidebar()
    st.title("Campus Event Management")
    if role == "Requester":
        ui_request.render_request_form()
    else:
        render_reviewer()
    st.divider()
    ui_request.render_schedule()


main()
