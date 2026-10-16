# Clinic Booking: practice project

A small appointment-booking API for a medical clinic. It is the shared practice
project for the AI Tools training (Track 0: Shared Fundamentals). Use it to
practice the full loop: read a ticket, reproduce, fix, open a PR, review, merge.

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
| `app/scheduling.py` | Slot generation, booking validation, overlap check |
| `app/static/index.html` | The frontend: one HTML file, vanilla JS, calls the API with `fetch` |
| `app/fees.py` | Consultation, late-cancel and no-show fees (integer cents) |
| `app/store.py` | Seed doctors/patients; appointments written through to SQLite |
| `app/config.py` | Business hours and settings read from the environment |
| `scripts/seed_demo.py` | Books demo appointments through the API |
| `data/seed.json` | Doctors and patients loaded at startup |
| `docs/business-rules.md` | What the clinic says the system should do |
| `docs/references/` | Code, git and testing conventions |
| `docs/templates/` | Ticket (feature/bug/chore), PRD, spec, MR, test and status report templates |
| `.claude/skills/` | `/ticket`, `/prd`, `/spec`, `/mr`, `/report` |
| `tickets/` | Your backlog. Each ticket is imperfect on purpose |
| `PRACTICE.md` | How to use this repo with the role-play drills |

## Rules of the practice

1. One ticket, one branch, one PR.
2. A bug fix needs a test that failed before and passes after.
3. Do not open `.instructor/`. It holds the answer key. Use it only to grade yourself after a drill.
4. AI output is a proposal until you have run it.
