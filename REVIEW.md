# PR Review Guidelines

Review instructions for Claude Code Review. Auto-discovered at the repository root.

## Review Passes

Run three passes over the diff and tag every finding with its pass: `[Bugs]`, `[Security]`, `[Compliance]`. Report only; fix nothing in a review.

- **Bugs:** correctness and business logic, broken edge cases, subtle regressions, data integrity and transaction safety, API contracts and validation, error handling, missing tests.
- **Security:** injection, authentication and authorization gaps, patient-data privacy, secrets in code or logs.
- **Compliance:** the change matches its ticket (acceptance criteria and test cases in `plans/tickets/T-NNN.md`), its plan (`plans/features/<feature>/plan.md` and `spec.md` when the branch carries one), `docs/business-rules.md`, and the conventions in `docs/references/` and `CLAUDE.md`. Also covers scope creep beyond the issue and significant maintainability issues.

## Severity and Important

- **Critical** — breaks behavior in production, corrupts or loses data, or exposes a secret or patient data. Should block merge.
- **High** — violates an acceptance criterion, business rule, or stated policy (auth gap, unsafe SQL, unapproved dependency, weakened tests). Should block merge.
- **Medium** — a real defect with limited blast radius: unhandled edge case, missing test coverage. A nit.
- **Low** — style, naming, or preference. A nit.

**Important** means Critical or High; Medium and Low are nits. Report at most five nits per review and summarize the rest as a count. Findings inform the human approver's call through branch protection — they never block a merge on their own.

## Clinic Booking Rules

Source of truth: `docs/business-rules.md`. Conventions: `docs/references/`.

**Correctness (`Bugs`)**
- Money is integer cents; percentages round half up via `fees._percent`. Flag `float` in fee, discount or price code.
- Datetimes are timezone-aware and UTC. Get "now" from `clock.now_utc()` through the module. Flag `datetime.now()`, `datetime.utcnow()` and naive values. Convert for display with `scheduling.to_local()`.
- Appointment status changes only through `routes._move()`. Flag direct assignment such as `appt.status = "cancelled"`.
- Business-rule failures raise `DomainError`, not `HTTPException`.
- Every mutation calls `store.save()` or `store.delete()`.
- Scheduling rules hold: no overlap with the 12:00-13:00 lunch break, bookings in the future and at most 60 days ahead, the 24h cancellation boundary, DST days.

**Security and privacy (`Security`)**
- Every route needs a session (router-level `auth.current_user`); admin or destructive routes add `dependencies=ADMIN` (`auth.require_role("admin")`). Auth fails closed when `AUTH_SECRET` is unset and compares with `hmac.compare_digest`.
- Never log, echo or return a password, hash or session value, and never give them a default value in code, tests or docs. No `.env`, `data/*.db` or real secret is committed (`git ls-files | grep -E '\.env$|\.db$'` must print nothing).
- Validate untrusted input with bounds (`min_length`, `max_length`, `ge`, `le`) in Pydantic models; reject naive datetimes; cap `page_size` at 100 and bound every new query parameter. An unknown ID is a 404, not a crash.
- SQL lives in `app/store.py`, binds every value with `?`, and is never built with f-strings, `%`, `+` or `.format()`.
- In `app/static/index.html`, API data goes through `esc()` or `textContent`. Flag `innerHTML`, `outerHTML` and `insertAdjacentHTML` with API data, and unescaped API values passed to helpers that take raw HTML.
- Errors never echo raw user input, internal paths or tracebacks. No wildcard CORS (`allow_origins=["*"]`) or debug mode in committed config.
- Fake data only in code, seed data, fixtures, tests and the UI: no real names, phones, emails or IDs.

**Data and dependencies (`Bugs`, `Compliance`)**
- SQLite through the `store` layer only. Flag a new ORM or pip dependency.
- Preserve data integrity and scheduling rules when stored shapes change.

**Tests (`Bugs`)**
- Bug fixes ship a regression test that fails before the fix. New routes have a `TestClient` test. Cover success, failure, authorization and edge cases (30 vs 60 minute slots, odd-cent rounding, insured vs uninsured).
- Flag skipped, deleted or weakened tests.

**Scope and spec (`Compliance`)**
- Follow the issue's acceptance criteria and test cases; keep the PR to that one issue.
- When the feature carries `plans/features/<name>/plan.md` and `spec.md`, the implementation matches them, or the plan is updated in the same PR.
- Branch (`<type>/<N>-<slug>`) and commits (`(#N)`) carry the issue number; a missing one is a nit (Low).
- Items marked `OPEN QUESTION` in `docs/business-rules.md` are not decided in code.

## Review Standards

- Focus on defects introduced or worsened by the PR; do not flag pre-existing issues the diff does not touch.
- Report only concrete, actionable findings with credible impact; verify each against the code and drop whatever evidence does not back.
- Do not invent requirements or flag subjective style preferences. Cap nits at five per review and summarize the rest as a count.
- Do not report: generated files, `.venv/`, `__pycache__/`, cache directories, and anything CI or Ruff already enforces.
- Do not claim tests passed without evidence.
- Do not modify code or push fixes during review unless explicitly requested.

## Feedback Loop

- When the same mistake class is flagged for the second time, propose the wording to add it to `CLAUDE.md`; review reads `CLAUDE.md`, so it is caught from the next PR onwards.
- Flag changes that make `CLAUDE.md` outdated as a Compliance finding (Low).

## Findings Format

One line per finding — inline comment for line-level findings, one summary comment for the rest:

`[severity] [pass] path:line — problem — concrete failure case — suggested fix`

- **Severity:** Critical, High, Medium, or Low. **Pass:** Bugs, Security, or Compliance.
- **Issue:** what is wrong and under what conditions. **Impact:** why it matters. **Fix:** a practical recommendation.

If no actionable issues are found, state that clearly without claiming the code is bug-free.
