# CLAUDE.md

## Project

Clinic Booking is a FastAPI training project using fake data only.

- Business rules: `docs/business-rules.md` — source of truth.
- Project structure and setup: `README.md`.
- Coding, testing and git conventions: `docs/references/`.
- Work tracking: GitHub issues. `plans/archive/` is a read-only archive of T-001 to T-017.
- Planned work: Markdown in `plans/` is the source of truth; `/push-tickets` and `/sync-tickets` link it to issues (`docs/references/ticket-sync.md`).

## Commands

```bash
pip install -r requirements.txt
cp .env.example .env
set -a; source .env; set +a
uvicorn app.main:app --reload
pytest
```

The app reads its settings (including `AUTH_SECRET`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`) from the environment, so source `.env` before starting it.
The UI is at `/`, Swagger at `/docs`. The database path is configurable via `DB_PATH`.
Run `DEMO_USERNAME=... DEMO_PASSWORD=... python scripts/seed_demo.py` with the server running to seed demo data (log in first and change the seeded admin's password).

## Workflow

Start in Plan Mode. Then follow the steps that apply:

| # | Step | Command | Description |
|---|------|---------|-------------|
| 1 | Plan Mode | — | Analyze the requirement, explore the codebase, identify ambiguities. |
| 2 | Create Ticket | `/create-ticket` | Structured Markdown ticket with acceptance criteria and test cases. |
| 3 | Sprint Prepare | `/sprint-prepare` | Propose a Sprint Goal and feasible scope from estimates; the team approves it. |
| 4 | Push Tickets | `/push-tickets` | Publish approved tickets to GitHub Issues. |
| 5 | Plan Work | `/plan-work` | Per ticket, before coding: approach, dependencies, risks and testing; you approve it. |
| 6 | Implement Ticket | `/implement-ticket` | Implement, run tests, report evidence. |
| 7 | Create PR | `/pr` | PR with the ticket reference and implementation summary. |
| 8 | Review PR | `/review-pr` | Review diff, acceptance criteria, security and tests; fix and re-review. |
| 9 | Merge & Deliver | — | Merge after approval and CI; deploy per the release process. |

- Do not implement tickets outside the approved sprint scope or change that scope without team agreement.
- Run `/sync-tickets` at lifecycle checkpoints to bring issue status back to Markdown.
- Follow the instructions in the relevant `.claude/` skills and agents.
- Resolve blocking questions before implementation. Never invent answers to open business-rule questions.
- Branches and commits follow `docs/references/git-conventions.md` (`feat|fix|chore|docs/...`, `<type>: <what> (#N)`). Never name a branch `claude/*`.
- Keep changes scoped to the current issue. Record unrelated findings separately.
- Ask before creating, editing, or commenting on GitHub issues, and before each push or merge.
- Run relevant tests before finishing. Bug fixes must include regression tests.

## Critical Constraints

- Use fake data only. Never commit `.env`, real credentials, or a real `AUTH_SECRET` or admin password.
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
