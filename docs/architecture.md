# Campus Event Management System: Proposed Architecture

**Stack:** Python 3.11+ · Streamlit · SQLite
**Builds on:** [solution-design.md](solution-design.md) (components, data flows, data model). This document fixes the **architecture style** and the **folder structure**, with the reason each folder exists.

---

## 1. Architecture Style

A **layered architecture in the "clean architecture" style**, kept small for a 90-minute prototype:

```
┌──────────────────────────────────────────────────────────────┐
│  PRESENTATION      app.py · pages/ · cems/ui/                │  Streamlit: show data, collect input
├──────────────────────────────────────────────────────────────┤
│  APPLICATION       cems/services/                            │  Use cases: one method = one business
│                                                              │  operation = one transaction
├──────────────────────────────────────────────────────────────┤
│  DOMAIN            cems/domain/                              │  Business rules. Pure Python, no I/O.
├──────────────────────────────────────────────────────────────┤
│  INFRASTRUCTURE    cems/data/                                │  SQLite: connection, transactions, SQL
└──────────────────────────────────────────────────────────────┘
                          ▼
                   var/campus_events.db
```

**Why this style**

| Concern | How the architecture addresses it |
|---|---|
| Business rules must be correct and explainable | They live in one pure layer (`domain/`) that can be tested without a UI or DB. |
| The brief judges flows, validations and conflict handling | Each flow is one service method; each rule is one function you can point to in the demo. |
| A team of several people building in parallel in 90 minutes | One folder per layer, one owner per folder, so merge conflicts are rare. |
| AI-generated code must be understood | Small, single-purpose modules; dependencies only point downward, so any file can be read on its own. |
| Streamlit and SQLite might be swapped later | Only `pages/` and `ui/` know about Streamlit, and only `data/` knows about SQLite. |

**Dependency rules** (enforced in code review)

1. `pages/` and `ui/` → may import `services/` and `domain/` types only. **Never** `data/` or `sqlite3`.
2. `services/` → may import `domain/` and `data/`.
3. `data/` → may import `domain/` (to build entities from rows).
4. `domain/` → imports **nothing** from the project, and only the standard library.
5. `config.py` → may be imported by anyone; imports nothing from the project.

---

## 2. Folder Structure

```
campus-event-management/
│
├── app.py                          # Streamlit entry point
├── pages/                          # one Streamlit page per user goal
│   ├── 1_Request_Event.py
│   ├── 2_My_Requests.py
│   ├── 3_Review_Queue.py
│   ├── 4_Venues_and_Availability.py
│   └── 5_Admin_and_Demo.py
│
├── cems/                           # the application package ("Campus Event Management System")
│   ├── __init__.py
│   ├── config.py                   # all tunable settings in one place
│   │
│   ├── domain/                     # business rules (no Streamlit, no SQLite)
│   │   ├── __init__.py
│   │   ├── models.py               # entities and value objects: Venue, EventRequest, VenueBlock, User, TimeSlot
│   │   ├── enums.py                # EventStatus, Role, EventType, VenueType, BlockReason, ReasonCode
│   │   ├── state_machine.py        # allowed status transitions; HOLDING_STATUSES
│   │   ├── availability.py         # the overlap rule (half-open intervals, optional buffer)
│   │   ├── validators.py           # request/block rules → Violation or Warning
│   │   ├── permissions.py          # who can do what
│   │   ├── clock.py                # Clock interface, SystemClock, FixedClock
│   │   └── errors.py               # Violation, Warning, reason codes → message templates
│   │
│   ├── services/                   # use cases (one transaction per public method)
│   │   ├── __init__.py
│   │   ├── result.py               # Result type: ok / fail(reasons) / warnings
│   │   ├── request_service.py      # submit, withdraw, preview availability
│   │   ├── review_service.py       # approve, reject
│   │   ├── lifecycle_service.py    # cancel confirmed event
│   │   ├── block_service.py        # preview impact, create block (with cascade), release block
│   │   ├── query_service.py        # read models for pages (schedules, queues, history)
│   │   ├── notification_service.py # in-app notifications (bonus)
│   │   └── container.py            # wires clock + DB + services together (simple dependency injection)
│   │
│   ├── data/                       # persistence (the only code that touches SQLite)
│   │   ├── __init__.py
│   │   ├── db.py                   # connection factory, Unit of Work (BEGIN IMMEDIATE, commit/rollback)
│   │   ├── schema.sql              # tables, CHECK constraints, indexes
│   │   ├── bootstrap.py            # create schema if missing, seed, recover from a corrupt file
│   │   ├── seed_data.json          # initial campus data from the brief (+ demo users)
│   │   └── repositories/
│   │       ├── __init__.py
│   │       ├── venue_repo.py
│   │       ├── event_repo.py       # includes find_holding_overlaps()
│   │       ├── block_repo.py
│   │       ├── user_repo.py
│   │       ├── history_repo.py
│   │       ├── notification_repo.py
│   │       └── settings_repo.py    # demo clock and other runtime settings
│   │
│   └── ui/                         # shared Streamlit helpers (no business logic)
│       ├── __init__.py
│       ├── session.py              # current user / role in st.session_state, flash messages
│       ├── components.py           # status badges, schedule table, reason list, confirm dialogs
│       └── formatting.py           # date/time and status display formats
│
├── tests/
│   ├── conftest.py                 # fixtures: temp SQLite file, FixedClock, seeded container
│   ├── domain/                     # fast unit tests: overlap, validators, state machine, permissions
│   ├── services/                   # flow tests against a real temp DB
│   └── data/                       # schema + seed integrity tests
│
├── scripts/
│   └── reset_db.py                 # reset the database from the command line before a demo or test run
│
├── docs/                           # requirements, review, design, architecture, user stories, pitch
├── var/                            # runtime files (SQLite DB, logs). Git-ignored, created on first run
│   └── .gitkeep
├── .streamlit/
│   └── config.toml                 # Streamlit theme and server settings
│
├── requirements.txt                # pinned runtime + test dependencies (streamlit, pytest)
├── pytest.ini                      # test discovery and paths
├── .gitignore                      # var/*.db, __pycache__, .venv, .pytest_cache
└── README.md                       # run steps, assumptions, scope, trade-offs, limitations, pitch
```

---

## 3. Why Each Folder Exists

### Top level

| Path | Why it exists |
|---|---|
| `app.py` | Streamlit needs one entry script. It holds only the shell: page setup, first-run bootstrap, the role switcher and the demo-date banner. Keeping it thin means one `streamlit run app.py` command starts everything. |
| `pages/` | Streamlit's built-in multipage convention: each file becomes a sidebar page automatically, with no routing code. **One page per user goal** (request, track, review, manage venues, admin) mirrors the personas, which makes the demo easy to narrate. The numeric prefixes set the menu order. |
| `cems/` | All real logic sits in an importable package, separate from Streamlit's page scripts. Tests and scripts import it the same way pages do, and it keeps the root folder readable. |
| `tests/` | Mirrors the package layers so you can find a rule's tests next to the rule's layer. Kept outside the package so tests are never shipped or imported by the app. |
| `scripts/` | Command-line chores that don't belong in the UI or the app package, such as a reliable DB reset before rehearsal. Reduces live-demo risk (review F2). |
| `docs/` | Everything the brief requires besides code: assumptions, scope, trade-offs, limitations, pitch material. Evaluators read it, and the git history shows how it evolved. |
| `var/` | Separates **runtime data** from **source code**. The DB file is generated, so it's git-ignored; that avoids merge conflicts on a binary file and stale demo data in commits. `.gitkeep` keeps the empty folder in git. |
| `.streamlit/` | Streamlit reads its config from here (theme, disabling usage stats). Checked in so every team member sees the same app. |
| `requirements.txt` / `pytest.ini` / `.gitignore` | Reproducible setup with a single install command; consistent test runs; keeps generated files out of git. |

### Inside `cems/`

| Path | Why it exists |
|---|---|
| `config.py` | One home for tunable values (DB path, default demo date, max duration, buffer minutes, max open pending per user). Changing a business parameter is then a one-line change, not a search through the code. |
| `domain/` | **The heart of the system.** Every business rule from the brief lives here as plain Python with no I/O, so it can be tested in milliseconds and explained in isolation. It doesn't depend on Streamlit or SQLite, so neither can leak into the rules. |
| `domain/state_machine.py` | Kept separate because "which status changes are legal" is the single most important consistency rule, and a separate file makes it easy to find during evaluator questions. |
| `domain/availability.py` | Holds the one overlap rule that submit, approve and block all reuse, so the logic can't be duplicated and drift. |
| `domain/clock.py` | Makes "now" injectable, so the August 2026 seed data and the tests behave consistently (review H1). |
| `services/` | The **use-case layer**: one file per business area, one method per user action. This is where transactions begin and end, permissions are checked and domain rules are combined. Pages stay thin, and flows can be tested without a browser. |
| `services/result.py` | A shared shape for "succeeded / failed with these reasons / succeeded with warnings", so every page shows outcomes the same way and tests check reason codes, not message text. |
| `services/container.py` | One place that builds services with their clock and DB. Tests swap in a temp DB and a fixed clock here, without patching code. |
| `data/` | The **only** place that knows SQLite exists. Isolates SQL, connection handling and transactions, so persistence bugs and locking issues have one place to look. |
| `data/repositories/` | One small module per table group keeps SQL short and owned. `event_repo.find_holding_overlaps()` is the single query behind conflict detection. |
| `data/schema.sql` | The schema as a plain SQL file is readable by everyone (including evaluators), reviewable in diffs, and serves as a database-level safety net (CHECK constraints). |
| `data/seed_data.json` | Keeps the brief's initial data **separate from code**, so adding demo records doesn't mean editing Python. Seeds are loaded through the same validators as user input (E23). |
| `data/bootstrap.py` | Makes first launch and recovery automatic: create, seed, or rebuild. The app always starts in a known state. |
| `ui/` | Shared Streamlit widgets and formatting used by several pages, kept out of `pages/` to avoid copy-paste. Holds no business logic, only how to *display* domain data. |

### Deliberately not included

| Not present | Why |
|---|---|
| `api/` (REST layer) | The brief needs a local UI only. The service layer is already the API boundary if one is added later. |
| `migrations/` | A prototype with a reset button doesn't need schema versioning. Listed as next step. |
| An ORM (SQLAlchemy) | The standard library `sqlite3` with parameterised SQL is enough, has no extra dependency, and the SQL stays visible. |
| `auth/` | Authentication is optional in the brief; a role switcher is a documented trade-off. |
| `Dockerfile` / CI configs | The brief forbids complex infrastructure; `pip install` + `streamlit run` is enough. |

---

## 4. Request Path Through the Folders (example: Submit)

```
pages/1_Request_Event.py           user clicks Submit
  └─► cems/services/request_service.py   submit_request(user, form)
        ├─► cems/domain/validators.py         field, time, capacity rules (pure)
        ├─► cems/data/db.py                   BEGIN IMMEDIATE
        ├─► cems/data/repositories/event_repo.py   find_holding_overlaps()
        ├─► cems/domain/availability.py       overlap decision (pure)
        ├─► event_repo.insert() + history_repo.insert()
        └─► COMMIT → Result.ok / Result.fail(reasons)
  ◄── page renders Result via cems/ui/components.py
```

---

## 5. Ownership Map (for the team and the git history)

| Folder | Owner | Can start immediately? |
|---|---|---|
| `cems/domain/` + `tests/domain/` | Member 1 | Yes (no dependencies) |
| `cems/data/` + `tests/data/` + `scripts/` | Member 2 | Yes (schema from design doc) |
| `cems/services/` + `tests/services/` | Member 3 | After the domain models are stubbed (≈ 15 min) |
| `app.py`, `pages/`, `cems/ui/`, `README.md`, `docs/` pitch | Member 4 | Yes, against stubbed `Result` objects |

Shared files (`config.py`, `requirements.txt`) are created in the **first commit** by one person, so later changes are small edits rather than conflicting creations.
