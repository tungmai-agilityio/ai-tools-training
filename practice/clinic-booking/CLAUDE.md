# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Clinic Booking: a FastAPI training project with fake data only. The spec is `docs/business-rules.md`, the backlog is in `tickets/`, and the file layout is in `README.md`.

## Commands

```bash
pip install -r requirements.txt && cp .env.example .env && set -a; source .env; set +a
uvicorn app.main:app --reload       # UI at /, Swagger at /docs; appointments persist in data/clinic.db (DB_PATH)
python scripts/seed_demo.py         # demo data through the API (server must be running)
pytest                              # full suite; single test: pytest tests/test_fees.py::test_name
```

## Workflow

- References: `docs/references/` (code, git, testing conventions). Templates: `docs/templates/` (tickets, PRD, spec, MR, reports).
  Skills `/ticket`, `/prd`, `/spec`, `/mr`, `/report` fill them in.
- One ticket gets one branch (`fix/T-00N`), one commit (`fix: <what> (T-00N)`), and one GitLab merge request into `develop`.
- Every bug fix comes with a test that fails before the fix and passes after it. Run `pytest` before you call anything done.
- When a ticket is vague or contradicts `docs/business-rules.md`, ask before coding. If an item there is marked OPEN QUESTION, don't decide it in code.

## Conventions

- Money is integer cents, and percentages round half up. Never use floats for money.
- Datetimes are always timezone-aware and stored in UTC. Business-hour logic converts to clinic time with `scheduling.to_local()`.
- Get "now" from `clock.now_utc()`, called through the module so the tests can freeze it.
- Business-rule failures raise `DomainError(message, status)`, which defaults to 409. Don't raise `HTTPException`.
- Lifecycle changes go through `routes._move()`, which checks the `TRANSITIONS` map.
- Tests: `DB_PATH` is `:memory:`, the `client` fixture resets the store, and `tests/helpers.book()` creates appointments. Time is frozen at Tue 2026-10-13 10:00 New York time; set `now["value"]` to move it. Name tests after the behaviour, like `test_insured_gets_20_percent_off`.

## Never do

- **NEVER open, read, or grep `.instructor/`.** It holds the answer key.
- Don't add real patient or client data, and don't commit `.env` or a real `ADMIN_TOKEN`.
- Don't weaken or delete an existing test to get the suite green.
- Don't add a dependency or an ORM. Appointments persist in SQLite (`DB_PATH`) via stdlib `sqlite3`, written through `store.save()`/`store.delete()`; doctors and patients stay seed-only.
- Don't fix more than the current ticket. Note anything else you find for a separate ticket.
