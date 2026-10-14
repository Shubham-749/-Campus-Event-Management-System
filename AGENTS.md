# Agent Directives: Campus Event Management System

Instructions for every AI coding agent (Claude Code, GitHub Copilot, others) working in this repo. Six people develop **in parallel**, each with their own agent. Follow these rules exactly. They exist so that parallel work merges cleanly.

## 1. First, Know Who You Work For

At the start of every session, establish which team member (**P1–P6**) you're working for. If the developer hasn't said, **ask before editing anything**. Your ownership determines which files you may change.

| Person | Owns (may edit) | Builds |
|---|---|---|
| P1 | `db.py` | SQLite schema, seed data, query/update functions |
| P2 | `rules.py`, `test_rules.py` | Pure business rules + tests |
| P3 | `workflow.py` | Use cases: submit, approve, reject, cancel |
| P4 | `app.py`, `ui_request.py` | Streamlit shell, role switcher, request form, schedule table |
| P5 | `ui_review.py` | Reviewer queue, approve/reject, cancel screens |
| P6 | `requirements.txt`, `.gitignore`, `README.md`, `notifications.py`, repo skeleton | Integration, QA, docs, bonus notifications |

`docs/`, `AGENTS.md`, `CLAUDE.md` and `.github/` change only when the developer explicitly asks.

## 2. Hard Rules

1. **Edit only your owner's files.** If a change is needed in someone else's file, **don't make it**. Stop and tell your developer exactly what's needed (file, function, why) so they can ask the owner.
2. **Never change a function signature in the interface contract (Section 4)** without your developer's confirmation. Others are coding against it right now.
3. **Build only the MVP scope** in [docs/mvp.md](docs/mvp.md). Don't add features, screens, states, tables or dependencies that aren't listed. Extra scope is a defect here.
4. **Stack is fixed:** Python 3.11+, Streamlit, standard library `sqlite3`, pytest. No ORM, no web framework, no cloud services, no external APIs, no new packages without P6's agreement.
5. **Layer boundaries:**
   - Only `db.py` (and `notifications.py` for its own table) imports `sqlite3`.
   - Only `app.py` and `ui_*.py` import `streamlit`.
   - `rules.py` imports nothing from the project. It's pure Python, with no I/O.
   - UI files call `workflow.py` for any state change, never `db.py` write functions. They may call `db.list_venues()` and `db.list_events()` for display.
6. **Never commit** `var/*.db`, virtual environments, `__pycache__`, or secrets.
7. **Never force-push, rebase shared history, or rewrite `main`.**

## 3. Business Rules (source of truth: [docs/mvp.md](docs/mvp.md))

- An event has a venue, a start and an end. Times are ISO strings `YYYY-MM-DDTHH:MM`, local time, minute precision.
- Statuses: `PENDING`, `CONFIRMED`, `REJECTED`, `CANCELLED`, `BLOCKED` (maintenance and renovation blocks are rows in `events`).
- **Holding statuses** (occupy the venue): `PENDING`, `CONFIRMED`, `BLOCKED`. Venue release on reject or cancel is automatic because availability is computed from status. **Don't add a separate "booked" flag.**
- **Overlap** uses half-open intervals: conflict when `a_start < b_end and b_start < a_end`. Back-to-back bookings are allowed.
- A request is refused, with **all** reasons returned together, when: end ≤ start; attendance ≤ 0 or > venue capacity; it overlaps any holding row on the same venue.
- Allowed transitions: `PENDING → CONFIRMED` (approve; re-check overlaps first), `PENDING → REJECTED` (reason required), `CONFIRMED → CANCELLED` (reason required). Everything else is refused.
- **No past-date validation** in the MVP (documented assumption).
- Reason messages are specific, e.g. `"Expected attendance 80 exceeds Innovation Lab capacity of 60"`, `"Conflicts with CONFIRMED event on 2026-08-04 10:00–12:00"`.

**Seed data** (from the brief): Seminar Hall A (Seminar Hall, 120), Main Auditorium (Auditorium, 500), Conference Room C (Conference Room, 40), Central Amphitheatre (Open Venue, 300), Innovation Lab (Computer Lab, 60). Confirmed events: Seminar Hall A 2026-08-04 10:00–12:00; Innovation Lab 2026-08-06 14:00–17:00. Block: Conference Room C 2026-08-04 09:00–18:00 (Renovation).

## 4. Interface Contract

Code against these exactly. Until the owner merges, use the stub in the skeleton.

| File | Functions |
|---|---|
| `db.py` | `init_db(reset=False)`, `list_venues()`, `get_venue(venue_id)`, `list_events(venue_id=None)`, `find_overlaps(venue_id, start, end, exclude_id=None)` (holding statuses only), `insert_event(title, event_type, venue_id, start, end, attendance, status)` → id, `update_status(event_id, status, reason=None)`, `get_event(event_id)` |
| `rules.py` | `overlaps(a_start, a_end, b_start, b_end)` → bool, `validate_request(venue, start, end, attendance, conflicts)` → list of reason strings (empty = valid), `can_transition(from_status, action)` → bool |
| `workflow.py` | `submit_request(form)` → `(ok, reasons, event_id)`, `approve(event_id)` → `(ok, reasons)`, `reject(event_id, reason)` → `(ok, reasons)`, `cancel(event_id, reason)` → `(ok, reasons)` |
| `ui_request.py` | `render_request_form()`, `render_schedule()` |
| `ui_review.py` | `render_review_queue()`, `render_cancel_panel()` |
| `notifications.py` (bonus) | `notify(event_id, message)`, `list_notifications()`, `mark_all_read()` |

Rows are returned as plain `dict`s. Expected business failures return `ok=False` with reasons; they don't raise exceptions.

## 5. Code Conventions

- Match the existing style; keep functions small, with type hints and a one-line docstring naming the business rule.
- Parameterised SQL only (`?` placeholders). Never build SQL with f-strings.
- Open a connection per function call, and close it, inside `db.py`. Don't cache connections (Streamlit reruns on other threads).
- In Streamlit, use `st.form` for submissions to avoid double-submits; call `st.rerun()` after a successful action.
- Don't add comments that restate the code.

## 6. Git Workflow

1. `git pull` before you start and before every push.
2. Work on a short branch named `p<N>/<story>` (e.g. `p2/mvp-6-tests`), or straight on `main` if the team agrees, since file ownership keeps conflicts rare.
3. Commit small and often. Message format: `<STORY-ID>: <what changed>` (e.g. `MVP-2: return capacity reason`). End messages with the attribution line the developer's tool requires.
4. **Merge order follows dependencies:** P1 and P2 → P3 → P4 and P5 → P6 bonus. Don't merge code that calls an unmerged function unless the stub exists.
5. Before merging `rules.py` or `workflow.py`: `pytest` must pass.
6. If a merge conflict touches a file you don't own, stop and tell your developer.

## 7. Definition of Done (for your owner's part)

- Meets the "Done when" for your person in [docs/mvp.md](docs/mvp.md) §7.3.
- `pytest` passes; `streamlit run app.py` starts without errors.
- No edits outside the owned files; no new dependencies; no signature changes.
- Any new assumption is reported to your developer for P6 to add to the README.

## 8. Run Commands

```
pip install -r requirements.txt
streamlit run app.py
pytest
```

## 9. Reference Docs

- [docs/mvp.md](docs/mvp.md): **build scope, team assignment, timeline** (read first)
- [docs/architecture.md](docs/architecture.md): target architecture after the MVP
- [docs/solution-design.md](docs/solution-design.md): components and data flows
- [docs/user-stories.md](docs/user-stories.md): full backlog (don't build beyond the MVP)
