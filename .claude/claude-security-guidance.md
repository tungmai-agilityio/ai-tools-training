# Clinic Booking security reference

The detailed security rules for this codebase, and how to review a change against them. `REVIEW.md` §4 lists the checks a reviewer runs; this file holds the rules behind them. No secrets in this file: it is sent with every security review.

## Threats
- The API is unauthenticated except admin routes: anyone who can reach it can book, cancel and read appointments.
- Admin routes (holidays, doctor time off, deletes) change data for every patient; a missing or bypassable guard is the worst case.
- Data is clinic appointments: even fake, treat names, reasons and times as patient data.
- The UI renders API data, so stored input reaches other users' browsers.

## Authentication and authorization
- Every admin or destructive route calls `routes.require_admin(x_admin_token)` as its first statement.
- `require_admin` fails closed when `ADMIN_TOKEN` is empty or unset, and compares with `hmac.compare_digest`, never `==`.
- Never log, echo or return the admin token, and never give it a default value in code, tests or docs.

## Input validation
- Request bodies are Pydantic models in `app/models.py` with bounds (`min_length`, `max_length`, `ge`, `le`) on every free-text and numeric field.
- Datetimes must be timezone-aware; reject naive values.
- List endpoints cap paging (`page_size` ≤ 100). Any new query parameter gets a bound.
- Validate IDs exist before acting; an unknown ID is a 404, not a crash.

## Injection
- SQL lives only in `app/store.py`, uses stdlib `sqlite3`, and binds every value with `?` placeholders.
- Never build SQL with f-strings, `%`, `+` or `.format()`, including for table or column names.

## Output and XSS
- `app/static/index.html` renders API data with `textContent` or through `esc()`. No `innerHTML`, `outerHTML` or `insertAdjacentHTML` with API data.
- Helpers that take raw HTML (title, hint, action) must never receive unescaped API values.

## Secrets
- Secrets come from the environment only (`app/config.py`). `.env.example` holds placeholders.
- Never commit `.env`, `data/*.db` or a real token.

## Data exposure
- Fake data only in code, `data/seed.json`, fixtures, tests and the UI: no real names, phones, emails or IDs.
- Business failures raise `DomainError` with a message written for reception staff. Errors never echo raw user input, internal paths or tracebacks.
- No wildcard CORS (`allow_origins=["*"]`) and no debug mode in committed config.

## Security-review procedure
1. List changed routes in the diff; check each admin or destructive one for `require_admin` first.
2. Grep the diff for `execute(`, `f"`, `%`, `.format(` near SQL; for `innerHTML`/`insertAdjacentHTML`; for `HTTPException`, `print(`, `logging` near tokens.
3. Check new model fields and query parameters for bounds and timezone awareness.
4. Run `git ls-files | grep -E '\.env$|\.db$'` (must print nothing) and `git log -p -S ADMIN_TOKEN` (no real value).
5. Scan new seed, fixture and test data for anything that looks real.
6. Report each finding with `path:line`, the attack or failure case, and the fix. Give a secret's location, never its value.
