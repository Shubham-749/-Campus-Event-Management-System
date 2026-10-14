# Campus Event Management System (MVP)

A Streamlit app that runs the full event-request lifecycle for campus venues:
**request → review → confirmed / rejected → cancel → venue released**, with conflict, capacity and maintenance-block checks.

Scope is the 15-minute MVP in [docs/mvp.md](docs/mvp.md). The target architecture is in [docs/architecture.md](docs/architecture.md).

## Run

Requires Python 3.11+.

```
python -m venv .venv
.venv\Scripts\activate          # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
streamlit run app.py
pytest
```

On first run, the SQLite database is created at `var/campus_events.db` (git-ignored) and seeded from the brief. The **Reset demo data** button in the sidebar deletes it and seeds it again.

## Seed Data

| Venue | Type | Capacity |
|---|---|---|
| Seminar Hall A | Seminar Hall | 120 |
| Main Auditorium | Auditorium | 500 |
| Conference Room C | Conference Room | 40 |
| Central Amphitheatre | Open Venue | 300 |
| Innovation Lab | Computer Lab | 60 |

- Confirmed: Seminar Hall A, 2026-08-04 10:00–12:00
- Confirmed: Innovation Lab, 2026-08-06 14:00–17:00
- Blocked: Conference Room C, 2026-08-04 09:00–18:00 (Renovation)

## Demo Script (about 2 minutes)

Start with **Reset demo data**. The role is **Requester** unless a step says otherwise.

| # | Action | Expected |
|---|---|---|
| 1 | Seminar Hall A, 4 Aug 2026 11:00–13:00, 50 people | Refused: conflicts with the CONFIRMED event 10:00–12:00 |
| 2 | Innovation Lab, any free slot, 80 people | Refused: attendance 80 exceeds capacity of 60 |
| 3 | Conference Room C, 4 Aug 2026 14:00–15:00 | Refused: unavailable (Renovation) 09:00–18:00 |
| 4 | Seminar Hall A, 4 Aug 2026 12:00 → 10:00, 0 people | Refused with **both** reasons listed together |
| 5 | Main Auditorium, 12 Aug 2026 09:00–17:00, 300 people | Accepted as **Pending**; shown in the schedule |
| 6 | Switch to **Reviewer** → Approve the request from step 5 | Becomes **Confirmed** |
| 7 | Cancel the seeded Seminar Hall A event, with a reason | Becomes **Cancelled**; the reason is shown in the schedule |
| 8 | Switch to **Requester** → resubmit step 1 | Accepted, because cancelling released the slot |
| 9 | (Optional) Reviewer → Reject a pending request with a reason, then resubmit the same slot | Accepted, because rejecting released the slot |

Back-to-back bookings are allowed (for example, Seminar Hall A 12:00–13:00 next to the 10:00–12:00 event). A back-to-back **Pending** request still holds its slot, so submit it *after* step 8, not before, or step 8 will conflict with it.

## Business Rules

- An event has a venue, a start and an end (`YYYY-MM-DDTHH:MM`, local time, minute precision).
- **Holding statuses** (occupy the venue): `PENDING`, `CONFIRMED`, `BLOCKED`. `REJECTED` and `CANCELLED` don't hold, so release is automatic.
- **Overlap** uses half-open intervals: a conflict exists when `a_start < b_end and b_start < a_end`.
- A request is refused, with all reasons returned together, when: end ≤ start; attendance ≤ 0 or > venue capacity; it overlaps any holding row on the same venue.
- Transitions: `PENDING → CONFIRMED` (approve, after re-checking for overlaps), `PENDING → REJECTED` (reason required), `CONFIRMED → CANCELLED` (reason required). Everything else is refused.
- Partial bookings, split bookings and alternative suggestions aren't offered (brief condition 9).

## Assumptions

1. **No past-date validation.** The seed data is dated August 2026, so a "today" check would block the demo.
2. **No login.** A sidebar role switcher (Requester / Reviewer) stands in for authentication. Anyone in the Reviewer role is an "appropriate user" to approve, reject or cancel.
3. **Cancel is done from the Reviewer view.** Requesters see their requests' status in the schedule.
4. **Maintenance blocks come from seed data.** They're stored as `BLOCKED` rows in `events`, so one overlap query covers both bookings and blocks. There's no block-management screen.
5. **Event type is free text.** Attendance must be a whole number greater than 0.
6. **Single local user.** No concurrency guarantees beyond SQLite's own.

## Architecture

| File | Responsibility | Owner |
|---|---|---|
| `app.py` | Streamlit shell: role switcher, reset, layout | P4 |
| `ui_request.py` | Request form and schedule table | P4 |
| `ui_review.py` | Review queue (approve/reject) and cancel panel | P5 |
| `workflow.py` | Use cases: submit, approve, reject, cancel | P3 |
| `rules.py` | Pure business rules: overlap, validation, transitions | P2 |
| `db.py` | SQLite schema, seed data, queries | P1 |
| `notifications.py` | Bonus: notification table, notify / list / mark read | P6 |
| `test_rules.py` | Rule tests (pytest) | P2 |

Layering: UI → `workflow.py` → `rules.py` + `db.py`. Only `db.py` and `notifications.py` import `sqlite3`, only `app.py` and `ui_*.py` import `streamlit`, and `rules.py` has no project imports.

## Testing Performed

- `pytest`: 43 rule tests pass. They cover overlap, containment, adjacent slots (allowed), pending and blocked rows blocking, rejected/cancelled rows not blocking, capacity, end before start, combined reasons and transitions. Different-venue isolation is enforced by `db.find_overlaps` and was checked in the integration run.
- Workflow integration: the demo script was run against `workflow.py` on a fresh database. All refusals return the expected reasons; approve, reject and cancel work; reject and cancel release the slot; repeated or invalid transitions are refused; a missing reason is refused.
- UI smoke test: Streamlit `AppTest` renders the Requester and Reviewer views without exceptions.

## Bonus: In-App Notifications (BONUS-1)

`notifications.py` stores notifications in its own table in the same database file, so **Reset demo data** clears it as well:

- `notify(event_id, message)`: records a notification
- `list_notifications()`: returns all notifications, newest first (each has `is_read`)
- `mark_all_read()`: clears the unread count

Wiring it into the app needs one `notify()` call after each successful approve, reject and cancel in `workflow.py` (P3), and a sidebar list with an unread count and a "Mark all read" button in `app.py` (P4).

## Out of Scope (deferred)

Block-management UI, withdrawing pending requests, past-date checks, multiple users and ownership, self-approval prevention, suitability warnings, audit history, concurrency guarantees and a pre-submit availability panel. See [docs/mvp.md §5](docs/mvp.md).
