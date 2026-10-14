# Copilot Instructions

Read and follow [AGENTS.md](../AGENTS.md) at the repo root. It's the shared directive for every team member's agent. The essentials:

- Six people build in parallel. Ask which person (P1–P6) you're working for, and **edit only that person's files** (ownership table in AGENTS.md §1). Needed changes in other files → tell the developer instead.
- Don't change function signatures in the interface contract (AGENTS.md §4).
- Build only the MVP in `docs/mvp.md`. Stack: Python, Streamlit, `sqlite3`, pytest. No new dependencies.
- Only `db.py` touches SQLite; only `app.py` / `ui_*.py` touch Streamlit; `rules.py` is pure Python.
- Holding statuses are `PENDING`, `CONFIRMED`, `BLOCKED`; overlap is `a_start < b_end and b_start < a_end` (back-to-back allowed).
- Parameterised SQL only. Commit messages: `<STORY-ID>: <change>`. Pull before push; never force-push.
