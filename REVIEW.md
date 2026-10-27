# PR Review Guidelines

Review instructions for Claude Code Review. Auto-discovered at the repository root.

## Review Priorities

Review changes for actionable defects, prioritizing:

1. Correctness and business logic.
2. Security, authorization, and patient-data privacy.
3. Data integrity, transactions, and migration safety.
4. API contracts, validation, and error handling.
5. Regression risks and missing tests.
6. Significant maintainability issues.

## Clinic Booking Rules

Source of truth: `docs/business-rules.md`. Conventions: `docs/references/`.

**Correctness**
- Money is integer cents; percentages round half up via `fees._percent`. Flag `float` in fee, discount or price code.
- Datetimes are timezone-aware and UTC. Get "now" from `clock.now_utc()` through the module. Flag `datetime.now()`, `datetime.utcnow()` and naive values. Convert for display with `scheduling.to_local()`.
- Appointment status changes only through `routes._move()`. Flag direct assignment such as `appt.status = "cancelled"`.
- Business-rule failures raise `DomainError`, not `HTTPException`.
- Every mutation calls `store.save()` or `store.delete()`.
- Scheduling rules hold: no overlap with the 12:00-13:00 lunch break, bookings in the future and at most 60 days ahead, the 24h cancellation boundary, DST days.
- Items marked `OPEN QUESTION` in `docs/business-rules.md` are not decided in code.

**Security and privacy**
- Admin or destructive routes call `require_admin()` first; it fails closed and compares with `hmac.compare_digest`.
- Never expose patient data, credentials or tokens through logs, errors or API responses. No secrets, `.env` or database files are committed.
- Validate untrusted input with bounds in Pydantic models; SQL is parameter-bound; API data is never rendered as raw HTML.

**Data and dependencies**
- SQLite through the `store` layer only. Flag a new ORM or pip dependency.
- Preserve data integrity and scheduling rules when stored shapes change.

**Tests**
- Bug fixes ship a regression test that fails before the fix. New routes have a `TestClient` test. Cover success, failure, authorization and edge cases (30 vs 60 minute slots, odd-cent rounding, insured vs uninsured).
- Flag skipped, deleted or weakened tests.

**Scope**
- Follow the issue's acceptance criteria and keep the PR to that one issue.

## Review Standards

- Focus on defects introduced or worsened by the PR.
- Report only concrete, actionable findings with credible impact.
- Avoid speculative concerns, subjective style preferences, and duplicate findings.
- Do not invent requirements or flag existing issues unrelated to the changes.
- Skip what linters catch (Ruff formatting, imports) and ignore `.venv/`, `__pycache__/` and cache directories.
- Do not claim tests passed without evidence.
- Do not modify code or push fixes during review unless explicitly requested.

## Findings Format

For each finding, provide:

- **Severity:** Critical, High, Medium, or Low.
- **Location:** File and relevant line.
- **Issue:** What is wrong and under what conditions.
- **Impact:** Why it matters.
- **Recommendation:** A practical fix.

Use inline comments for line-level findings and one summary comment for the rest. If no actionable issues are found, state that clearly without claiming the code is bug-free.
