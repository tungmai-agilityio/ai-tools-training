# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Clinic Booking: a FastAPI training project with fake data only. The spec is `docs/business-rules.md`, work is tracked as GitHub issues (`tickets/` is a read-only archive of T-001 to T-017), and the file layout is in `README.md`.

## Commands

```bash
pip install -r requirements.txt && cp .env.example .env && set -a; source .env; set +a
uvicorn app.main:app --reload       # UI at /, Swagger at /docs; appointments persist in data/clinic.db (DB_PATH)
python scripts/seed_demo.py         # demo data through the API (server must be running)
pytest                              # full suite; single test: pytest tests/test_fees.py::test_name
```

## Workflow

- References: `docs/references/` (code, git, testing conventions). Templates: `.github/ISSUE_TEMPLATE/` (feature, bug, chore issues) and `docs/templates/` (PRD, spec, ADR, test plan, reports).
- Features: `/ticket` (**business-analyst** drafts; no issue while a blocking question is open) → `/plan` (**planner**; user approves the plan) → `/implement` (**developer**; pauses on new requirements or decisions) → `/review` → `/pr`.
  Bugs: `/ticket` triage → `/fix` (`/plan` first if it needs design). Chores: `/ticket` → `/plan` if it spans modules → `/implement`.
- Skills, agents, commands and hooks live in the repo-root `.claude/`, so always open Claude Code at the repo root. Subagents live in `.claude/agents/`: **business-analyst** (requirements and issue draft), **planner** (implementation plan and testing strategy), **developer** (test-first implementation and fixes), and **code-reviewer** (independent correctness, security, and quality gate). If one is not registered, spawn a general-purpose agent whose prompt starts with "Read `.claude/agents/<name>.md` (repo root) and follow it exactly".
- One issue gets one branch (`feat/<N>-<slug>`, `fix/<N>-<slug>`, `chore/<slug>` or `docs/<slug>`), one commit (`<type>: <what> (#N)`), and one pull request into `develop` whose body says `Closes #N`. Status: open issue, `in-progress` label while worked on (`blocked` while waiting on a decision), closed by the merge.
- Ask before creating, editing or commenting on a GitHub issue, and before each push and merge.
- Every bug fix comes with a test that fails before the fix and passes after it. Run `pytest` before you call anything done.
- When an issue is vague or contradicts `docs/business-rules.md`, ask before coding. If an item there is marked OPEN QUESTION, don't decide it in code.

## Conventions

- Money is integer cents, and percentages round half up. Never use floats for money.
- Datetimes are always timezone-aware and stored in UTC. Business-hour logic converts to clinic time with `scheduling.to_local()`.
- Get "now" from `clock.now_utc()`, called through the module so the tests can freeze it.
- Business-rule failures raise `DomainError(message, status)`, which defaults to 409. Don't raise `HTTPException`.
- Lifecycle changes go through `routes._move()`, which checks the `TRANSITIONS` map.
- Tests: `DB_PATH` is `:memory:`, the `client` fixture resets the store, and `tests/helpers.book()` creates appointments. Time is frozen at Tue 2026-10-13 10:00 New York time; set `now["value"]` to move it. Name tests after the behaviour, like `test_insured_gets_20_percent_off`.

## Never do

- Don't add real patient or client data, and don't commit `.env` or a real `ADMIN_TOKEN`.
- Don't weaken or delete an existing test to get the suite green.
- Don't add a dependency or an ORM. Appointments persist in SQLite (`DB_PATH`) via stdlib `sqlite3`, written through `store.save()`/`store.delete()`; holidays and doctor time off persist the same way (T-014); doctors and patients stay seed-only.
- Don't fix more than the current ticket. Note anything else you find for a separate ticket.
