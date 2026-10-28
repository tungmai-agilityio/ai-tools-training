# CLAUDE.md

## Project

Clinic Booking is a FastAPI training project using fake data only. Open Claude Code at the repository root so `.claude/` loads.

- Business rules: `docs/business-rules.md` — source of truth.
- Setup, structure and settings: `README.md`. API and role rules: `docs/references/api.md`.
- Coding, testing and git conventions: `docs/references/`.
- Work tracking: GitHub issues; planned work is Markdown in `plans/` (`docs/references/ticket-sync.md`). `plans/archive/` is a read-only archive of T-001 to T-017.

## Commands

```bash
make install   # dependencies
make test      # pytest
make lint
make run       # uvicorn --reload
```

## Workflow

Start in Plan Mode, then follow the steps that apply:
`/create-ticket` → `/sprint-prepare` → `/push-tickets` → `/plan-work` → `/implement-ticket` → `/pr` → `/review-pr` → merge after approval and CI.

- Do not implement tickets outside the approved sprint scope or change that scope without team agreement.
- Resolve blocking questions before implementation. Never invent answers to open business-rule questions.
- Branches and commits follow `docs/references/git-conventions.md`. Never name a branch `claude/*`.
- Ask before creating, editing, or commenting on GitHub issues, and before each push or merge.

## Critical Constraints

- Use fake data only. Never commit `.env`, real credentials, or a real `AUTH_SECRET` or admin password.
- Never weaken or delete tests just to make the suite pass.
- Use SQLite via the existing `store` layer. Do not add an ORM or dependencies without approval.

## Key Implementation Rules

Examples in `docs/references/code-conventions.md`.

- Money is integer cents, percentages round half up. Never floats.
- Datetimes are timezone-aware, stored in UTC; convert with `scheduling.to_local()`.
- Get the time via `clock.now_utc()`, called through the module so tests can freeze it.
- Business-rule failures raise `DomainError`, not `HTTPException`; lifecycle changes go through `routes._move()`.
