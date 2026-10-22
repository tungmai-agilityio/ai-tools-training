# CLAUDE.md

## Project

Clinic Booking is a FastAPI training project using fake data only.

- Business rules: `docs/business-rules.md` — source of truth.
- Project structure and setup: `README.md`.
- Coding, testing and git conventions: `docs/references/`.
- Work tracking: GitHub issues. `tickets/` is a read-only archive of T-001 to T-017.

## Commands

```bash
pip install -r requirements.txt
cp .env.example .env
set -a; source .env; set +a
uvicorn app.main:app --reload
pytest
```

The app reads its settings (including `ADMIN_TOKEN`) from the environment, so source `.env` before starting it.
The UI is at `/`, Swagger at `/docs`. The database path is configurable via `DB_PATH`.
Run `python scripts/seed_demo.py` with the server running to seed demo data.

## Workflow

- Start in Plan Mode. Follow `/ticket` → `/plan` → `/implement` (or `/fix`) → `/review` → `/pr` as applicable.
- Follow the instructions in the relevant `.claude/` skills and agents.
- Resolve blocking questions before implementation. Never invent answers to open business-rule questions.
- Keep changes scoped to the current issue. Record unrelated findings separately.
- Ask before creating, editing, or commenting on GitHub issues, and before each push or merge.
- Run relevant tests before finishing. Bug fixes must include regression tests.

## Critical Constraints

- Use fake data only. Never commit `.env`, real credentials, or a real `ADMIN_TOKEN`.
- Never weaken or delete tests just to make the suite pass.
- Use SQLite via the existing `store` layer. Do not add an ORM or dependencies without approval.
- Follow `docs/business-rules.md` and the existing project architecture.

## Key Implementation Rules

- Money uses integer cents; percentages round half up. Never use floats for money.
- Datetimes must be timezone-aware and stored in UTC. Convert to clinic time using `scheduling.to_local()`.
- Get the current time through `clock.now_utc()`, called through the module (not imported by name) so tests can freeze it.
- Business-rule failures raise `DomainError`, not `HTTPException`; lifecycle changes must go through `routes._move()`.

## Repository Setup

Open Claude Code at the repository root so project-level `.claude/` configuration is loaded.
