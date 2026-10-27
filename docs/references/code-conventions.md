# Code conventions

The rules every change in Clinic Booking follows. CLAUDE.md has the short version; this file has the why and the examples.

## Language and layout
- Python 3.11+, FastAPI, pydantic v2, stdlib `sqlite3`. No ORM, no new dependency without a ticket that says so.
- One module per concern: `routes.py` (HTTP + lifecycle), `scheduling.py` (slots, validation), `fees.py` (money),
  `store.py` (persistence), `config.py` (settings), `clock.py` (time), `errors.py` (domain errors).
- The frontend is one file, `app/static/index.html`: vanilla JS, `fetch`, no build step, no framework.
- Before writing a helper, grep for one. `scheduling.overlaps()`, `scheduling.to_local()`, `fees.*` and
  `tests/helpers.book()` already exist.

## Naming and style
- PEP 8, 4-space indent, max ~110 chars per line. `snake_case` functions and variables, `PascalCase` classes,
  `UPPER_CASE` config constants.
- New code: type hints on every function signature. Return `None` explicitly in the hint.
- A new module starts with a one-line docstring saying what it owns. Functions get a docstring only when the name
  does not say everything (an edge case, a unit, a rule).
- Comments explain *why*, never *what*. A deliberate shortcut gets a `ponytail:` comment naming its ceiling:
  `# ponytail: one shared connection + lock, use a pool if write throughput matters`.

## Domain rules in code
| Topic | Rule | Wrong | Right |
|---|---|---|---|
| Money | Integer cents. Percentages round half up. | `fee * 0.8` | `fees._percent(fee, 80)` (integer math, half up) |
| Time | Timezone-aware, stored in UTC. Business hours in clinic time via `scheduling.to_local()`. | `datetime.now()` | `clock.now_utc()` (call through the module so tests can freeze it) |
| Errors | Business-rule failures raise `DomainError(message, status)` (default 409, 422 for bad input). | `raise HTTPException(...)` | `raise DomainError("Doctor is busy")` |
| Lifecycle | Status changes go through `routes._move()`, which checks `TRANSITIONS`. | `appt.status = "cancelled"` | `_move(appt, "cancelled")` |
| Persistence | Every endpoint that changes an appointment calls `store.save(appt)` (or `store.delete(id)`) before it returns. | mutate `store.appointments` only | `store.save(appt)` |
| Open questions | An item marked OPEN QUESTION in `docs/business-rules.md` is not decided in code. | guess | ask, note it in the ticket |

## Frontend (`app/static/index.html`)
- One file of vanilla JS and CSS: no framework, CDN, build step or new dependency.
- Colours come from the existing `:root` CSS variables (dark theme included), never hard-coded.
- Every API value rendered into HTML goes through `esc()`. Times show in `CLINIC_TZ` (America/New_York). Money arrives
  in cents and is only formatted, never calculated.
- WCAG 2.1 AA: keyboard accessible, visible focus, AA contrast in both themes, correct ARIA roles, no status by colour
  alone, no horizontal scroll from 375px to 1440px.

## API
- REST, JSON, plural nouns: `/appointments`, `/appointments/{id}/cancel`.
- Errors return `{"detail": "<human sentence>"}`. The message is shown to reception as-is, so write it for them.
- Every route needs a session (the router depends on `auth.current_user`); admin-only endpoints add `dependencies=ADMIN`, as `delete_appointment` does. Never log or echo a password or session value.

## Data and secrets
- Fake data only. No real names, phones, emails or IDs, ever.
- Never commit `.env`, `data/*.db` or a real `AUTH_SECRET`. New settings go in `config.py` and `.env.example`.

## Scope
- Change only what the ticket asks. Anything else you notice becomes a note for a new ticket.
