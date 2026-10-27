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
uvicorn app.main:app --reload
```

`.env` is read at startup, so there is nothing to source first.

Then open:

- http://127.0.0.1:8000/ for the web app (book, appointment list, today's schedule)
- http://127.0.0.1:8000/docs for the raw API (Swagger)

Every endpoint, the session and role rules, and the business checks are listed in
[docs/references/api.md](docs/references/api.md).

### Login settings

Set these in `.env` before the first start: the app loads that file itself, and variables already in the environment take precedence.

| Variable | Value | What it does |
|---|---|---|
| `AUTH_SECRET` | random string, 32+ characters | Signs session cookies. Empty refuses every login; shorter stops startup. |
| `ADMIN_USERNAME` | e.g. `admin` | The first admin, seeded only while no users exist. |
| `ADMIN_PASSWORD` | 12+ characters | The first admin must change it at first sign-in. |
| `COOKIE_SECURE` | `true` | Set to `false` only for plain-http local demos. |

**Sessions and lockout.** Login sets an 8-hour `HttpOnly`, `SameSite=Strict` cookie; five failed logins lock a username for 15 minutes.

**Accounts.** Create an admin or reset its password without putting it in `.env` (works when users already exist): `python scripts/seed_admin.py USERNAME` prompts for the password. Restart the server afterwards. Admins manage accounts from the web app.

Clinic holidays, doctor time off and revenue reports are handled through the API; the admin-only ones need an administrator login. The web app has a Revenue screen for administrators.

Appointments persist in SQLite (`DB_PATH`, default `data/clinic.db`); delete the file to start fresh. To fill the list with demo data, run:

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
| `docs/references/` | API reference, code, git and testing conventions |
| `docs/templates/` | PRD, spec, ADR, DDR, test plan, test and status report templates |
| `docs/decisions/` | ADR and DDR records |
| `plans/` | Markdown tickets, sprints and feature docs (source of truth for planned work); `archive/` holds the read-only tickets T-001 to T-017 |
| `.github/` | Issue templates (feature, bug, chore), PR template, workflows |
| `.claude/` | Claude Code config for this repo. Skills: `/create-ticket` → `/sprint-prepare` → `/push-tickets` → per ticket `/plan-work` → `/implement-ticket` → `/pr` → `/review-pr`, plus `/sync-tickets`; 3 subagents (business-analyst, planner, code-reviewer); commands; hooks that block forbidden Bash commands, ruff-fix edited `.py` files and notify on finish (`settings.json`). With `.mcp.json` (Playwright MCP), it loads when Claude Code is opened at the repo root |

## Rules of the practice

1. One issue, one branch, one PR.
2. A bug fix needs a test that failed before and passes after.
3. AI output is a proposal until you have run it.
