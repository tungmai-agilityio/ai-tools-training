# Clinic Booking: practice project

A small appointment-booking API for a medical clinic. It is the shared practice
project for the AI Tools training (Track 0: Shared Fundamentals). Use it to
practice the full loop: read an issue, reproduce, fix, open a PR, review, merge.

Fake data only. Never put real client or patient data in this repo.

## Run it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
set -a; source .env; set +a
uvicorn app.main:app --reload
```

Then open:

- http://127.0.0.1:8000/ for the web app (book, appointment list, today's schedule)
- http://127.0.0.1:8000/docs for the raw API (Swagger)

### Login settings
Set in `.env` before first start: `AUTH_SECRET` (random string of at least 32 characters that signs sessions; empty means login is refused, a shorter one stops startup),
`ADMIN_USERNAME` and `ADMIN_PASSWORD` (12+ characters; seed the first admin only while no users exist, who must change the
password at first sign-in). `COOKIE_SECURE=false` is for plain-http local demos only. `POST /auth/login` sets an 8-hour
`HttpOnly`, `SameSite=Strict` cookie; `POST /auth/logout` clears it; `GET /auth/me` shows who is signed in.
Five failed logins lock a username for 15 minutes.
Admins manage accounts with `GET/POST /users` and `PATCH /users/{id}` (`active`, `role`; sending `active: true` also unlocks).

Clinic holidays (`/holidays`) and doctor time off (`/doctors/{id}/time-off`) are managed in Swagger.
Adding or removing them needs an administrator login (staff get `403`, no session gets `401`).
Admin-only `GET /reports/revenue?from=YYYY-MM-DD&to=YYYY-MM-DD` returns consultation and penalty revenue per doctor and per day.
The web app shows it on the Revenue screen (`#revenue`): pick a date range (administrators only).

Appointments persist in SQLite (`DB_PATH`, default `data/clinic.db`) via stdlib `sqlite3`.
No ORM, no new dependency. Delete the file to start fresh. To fill the list with demo data
(you need 11+ appointments to see pagination), run in another terminal:

```bash
python scripts/seed_demo.py
```

## Test it

```bash
pytest
```

Optional browser smoke test for the web app (dev-only; skipped when Playwright is missing):

```bash
pip install -r requirements-dev.txt && playwright install chromium
pytest tests/test_ui_browser.py
```

The suite is green on a fresh clone. Green does not mean bug-free: the tests only
cover behaviour that already works.

## Layout

| Path | What it is |
|---|---|
| `app/routes.py` | HTTP endpoints and the appointment lifecycle |
| `app/scheduling.py` | Slot generation, booking validation, overlap check, holiday and time-off checks |
| `app/static/index.html` | The frontend: one HTML file, vanilla JS, calls the API with `fetch` |
| `app/fees.py` | Consultation, late-cancel and no-show fees (integer cents) |
| `app/store.py` | Seed doctors/patients; appointments, holidays and time off written through to SQLite |
| `app/config.py` | Business hours and settings read from the environment |
| `scripts/seed_demo.py` | Books demo appointments through the API |
| `data/seed.json` | Doctors and patients loaded at startup |
| `docs/business-rules.md` | What the clinic says the system should do |
| `docs/references/` | Code, git and testing conventions |
| `docs/templates/` | PRD, spec, ADR, DDR, test plan, test and status report templates |
| `docs/decisions/` | ADR and DDR records |
| `plans/` | Markdown tickets, sprints and feature docs (source of truth for planned work); `archive/` holds the read-only tickets T-001 to T-017 |
| `.github/` | Issue templates (feature, bug, chore), PR template, workflows |
| `.claude/` | Claude Code config for this repo. Skills: `/create-ticket` → `/sprint-prepare` → `/push-tickets` → per ticket `/plan-work` → `/implement-ticket` → `/pr` → `/review-pr`, plus `/sync-tickets`; 3 subagents (business-analyst, planner, code-reviewer); commands; hooks that block forbidden Bash commands, ruff-fix edited `.py` files and notify on finish (`settings.json`). With `.mcp.json` (Playwright MCP), it loads when Claude Code is opened at the repo root |

## Rules of the practice

1. One issue, one branch, one PR.
2. A bug fix needs a test that failed before and passes after.
3. AI output is a proposal until you have run it.
