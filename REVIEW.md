# REVIEW.md

Review instructions for Claude. This file is auto-discovered at the repository root.

---

## Always flag (Walkthrough Checklist)

Follow this review order: **Correctness → Tests → Readability → Security basics → Scope**.

### 1. Correctness (Domain & Business Rules)

- **Money as floats.** All monetary values must be integer cents. Percentages round half up. Flag any use of `float` for fees, discounts, or price calculations. The correct pattern is `fees._percent(fee, pct)`.
- **Naive datetimes.** Every `datetime` must be timezone-aware and stored in UTC. Flag `datetime.now()`, `datetime.utcnow()`, or any datetime without `tzinfo`. The correct entry point is `clock.now_utc()`.
- **Direct status mutation.** Appointment status must change through `routes._move()`, which enforces the `TRANSITIONS` map. Flag any direct assignment like `appt.status = "cancelled"`.
- **HTTPException instead of DomainError.** Business-rule failures must raise `DomainError(message, status)` (default 409, 422 for bad input). Flag any `raise HTTPException(...)` for domain logic.
- **Missing `store.save()` / `store.delete()`.** Every endpoint that mutates an appointment must call `store.save(appt)` or `store.delete(id)` before returning. Flag mutations that skip persistence.
- **Lunch break overlap.** No appointment may overlap 12:00–13:00 clinic time. Flag scheduling logic that ignores lunch.
- **Booking-limit bypass.** Bookings must be in the future and ≤ 60 days ahead. Flag any path that skips this check.
- **Open questions decided in code.** Items marked `OPEN QUESTION` in `docs/business-rules.md` must not be resolved in code without explicit approval. Flag any implementation that assumes an answer.

### 2. Tests (Coverage & Quality)

- **Missing regression test for bug fixes.** Every bug fix must ship a test that fails before the fix and passes after. Flag fix PRs without one.
- **New API route without an integration test.** Any new endpoint in `routes.py` must have at least one test exercising it through `TestClient`. Flag untested routes.
- **Weakened or deleted tests.** Never weaken, skip, or delete an existing test to get the suite green. Flag `@pytest.mark.skip`, removed assertions, or loosened conditions on previously passing tests.
- **Tests named after functions, not behaviour.** Test names should describe the behaviour: `test_insured_gets_20_percent_off`, not `test_fees_2`. Flag opaque names.
- **Missing edge-case coverage.** For scheduling and fee changes, check that the PR considers: DST switch days, lunch break, 30 vs 60 minute slots, exactly-24h cancellation boundary, weekends, 60-day limit, back-to-back appointments, insured vs uninsured, odd-cent rounding.

### 3. Readability & Maintainability

- **Type hints missing on new functions.** All new function signatures must have type hints, including explicit `-> None` returns. Flag untyped additions.
- **Duplicate helpers.** Before introducing a new utility, check for existing ones: `scheduling.overlaps()`, `scheduling.to_local()`, `fees.*`, `tests/helpers.book()`. Flag reinventions.
- **Error messages not user-facing.** API error `detail` strings are shown to reception staff as-is. Flag cryptic, developer-only, or empty error messages.
- **Needless complexity.** Flag speculative abstractions, unnecessary indirection, or over-engineered solutions.

### 4. Security Basics

Apply `.claude/claude-security-guidance.md` (rules and review procedure) and flag any violation. At minimum check:

- **Admin guard.** Admin or destructive endpoints call `require_admin()` first.
- **Injection and input.** SQL is parameter-bound; new inputs are validated and bounded.
- **XSS.** API data is never rendered as raw HTML.
- **Secrets.** No token, `.env` or database is committed, logged or echoed.
- **Data exposure.** Fake data only; errors don't leak input, paths or tracebacks.

### 5. Scope & PR Hygiene

- **Scope creep.** Each PR should address only its ticket. Flag changes outside the ticket scope — note them for a separate ticket instead.
- **New dependency without a ticket.** No new pip dependency or ORM. The project uses stdlib `sqlite3` only. Flag any added dependency.
- **Multi-ticket PRs.** One ticket = one branch = one PR. Flag PRs that bundle unrelated changes.
- **Branch and history.** Branch is `feat/T-0NN`, `fix/T-0NN`, `chore/<slug>`, or `docs/<slug>`, rebased on `develop`, with exactly one commit.
- **Non-conventional commit messages.** Commits must follow `<type>: <what changed> (T-0NN)` format. Types: `feat`, `fix`, `test`, `refactor`, `docs`, `chore`. Flag deviations.

---

## Always skip

- **Style nits a linter catches.** Ruff handles formatting and import order. Don't flag whitespace, trailing commas, or import sorting — the `lint-on-edit` hook covers these.
- **The default GitLab README boilerplate.** The root `README.md` still has GitLab template text. Don't flag it unless the PR explicitly touches it.
- **Virtual environment and cache directories.** Ignore `.venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`.
- **Existing code outside the PR's ticket scope.** If pre-existing code violates conventions but isn't part of this ticket, don't flag it. Note it for a future ticket at most.

---

## Tone and format

- Use **inline comments** for specific line-level issues.
- Use **one summary comment** for overall observations (architecture, missing tests, pattern violations).
- Be direct and constructive. Reference the relevant convention doc when flagging (e.g., "per `docs/references/code-conventions.md`, money must be integer cents").
- Prioritise correctness bugs and missing tests over style.
