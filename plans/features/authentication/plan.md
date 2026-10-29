# Plan: Authentication (T-019 to T-023, sprint S-002)

**Author:** Claude (draft, for maintainer edit)  **Status:** Implemented (T-019 to T-023 closed; approved 2026-10-27)  **Spec:** [spec.md](spec.md)  **Sprint:** [S-002](../../sprints/S-002.md)  **Decisions:** ADR-0001 to ADR-0003, DDR-0001 to DDR-0003

One approval of this file covers the whole feature: the per-ticket `/plan-work` step is skipped, each ticket's `## Plan` section points here and is set to `**Plan:** Approved`. Requirement changes still go back to `/create-ticket`; anything outside this plan needs a new question to a maintainer.

## 1. Waves and dependencies

| Wave | Ticket | Issue | Branch | Starts when | Blocks |
|---|---|---|---|---|---|
| 1 | T-019 login core | #39 | `feat/39-cookie-login` | now | everything |
| 2 | T-020 user management | tbd | `feat/<N>-user-management` | T-019 merged | T-022, T-023 (needs users) |
| 2 | T-021 route protection, CSP, retire `ADMIN_TOKEN` | tbd | `feat/<N>-route-protection` | T-019 merged | T-022 (hides admin UI), finishing |
| 2 | T-023 change / reset password | tbd | `feat/<N>-password-change` | T-019 merged; reset endpoint needs T-020's user lookup, which T-019 already provides | T-022 |
| 3 | T-022 login UI | tbd | `feat/<N>-login-ui` | early, against the spec contract | none |

T-023 does not wait for T-020: T-019 ships the user store helpers both use (section 2), so the two stay independent. Issue numbers are read from each ticket's Tracking section when its session starts.

## 2. Shared files and conflict avoidance

T-020, T-021 and T-023 all touch `routes.py`, `models.py` and `store.py`. To keep them apart:

- **T-019 lays the shared base** so later tickets only add: in `store.py` the `users` table plus `get_user`, `get_user_by_name`, `save_user`, `list_users`; in `models.py` `User` (no hash), `UserIn`, `LoginIn`, `SessionOut`; in `auth.py` `current_user`, `issue_session`, `set/clear_session_cookie`. Recommended: `current_user` also holds the `must_change_password` gate (403 except for change-password and `/auth/me`, via a parameter), so T-023 only adds endpoints and tests.
- **New routers, not edits to `routes.py`:** T-019 puts `/auth/login|logout|me` in `app/auth_routes.py`; T-020 puts `/users*` in `app/users.py`; T-023 puts `/auth/change-password` in `app/auth_routes.py` (one added function) and `/users/{id}/reset-password` in `app/users.py` (one added function, after T-020). Each router is included in `main.py` by its own ticket (one line each).
- **T-021 is the only ticket that edits existing handlers in `routes.py`** (swap `x_admin_token` for `require_role`), plus `main.py` middleware and `config.py` (removes `ADMIN_TOKEN`). `scripts/seed_demo.py` and the test login helper (`tests/helpers.py`) are T-021's.
- **Models:** each ticket adds its own models at the end of `models.py`; `ChangePasswordIn` and `ResetPasswordOut` belong to T-023.
- Order of merge inside wave 2 does not matter. The second PR to merge rebases on `develop` and re-runs `pytest`; the later PR owns resolving the conflict.
- `docs/business-rules.md` already has the Authentication section; tickets edit it only if behaviour differs from it.

## 3. Per-ticket approach and tests

**T-019 (M).** `config.py` settings (`AUTH_SECRET`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `COOKIE_SECURE` default true, lockout and TTL constants). scrypt hashing and HMAC-SHA256 cookie value carrying user id, `session_version` and expiry; time from `clock.now_utc()` called through the module. Login with generic `401` (dummy hash check for unknown users), `423` while locked, count reset on success, logout `204` idempotent, `/auth/me`. Seed first admin at startup per AC-6 to AC-6d; fail closed when `AUTH_SECRET` is empty. Failures raise `DomainError`. Tests: `tests/test_auth.py`, `tests/test_login.py` (TC-1 to TC-10, frozen clock, env override and fresh store for the seed cases). Docs: `.env.example` placeholders, README. Not protecting any route yet.

**T-020 (S).** `GET/POST /users`, `PATCH /users/{id}` (active, role); duplicate check case-insensitive `409`, weak password `422`, last-active-admin guard `409`, disabling bumps `session_version`, re-enable or unlock clears the lock. A temporary local `require_admin_user` in `users.py` using `current_user` until T-021 lands `require_role`; swapped for `require_role("admin")` in whichever PR merges second. Tests: `tests/test_users.py` (TC-1 to TC-5).

**T-021 (M).** `require_role("staff"|"admin")` as router-level dependency on the clinic router so new routes are protected by default; public list per spec. Remove `ADMIN_TOKEN` and `X-Admin-Token` from code, config, README, `CLAUDE.md`, `REVIEW.md`, CI text, docs and tests (only records describing the removal remain). Middleware: CSP header on every response, `Origin` check on unsafe methods. Tests: `tests/test_authorization.py` (parametrised over every route, TC-1 to TC-8) plus a source scan test. Existing tests get a login helper in `tests/helpers.py`; none weakened. `scripts/seed_demo.py` logs in. **CSP caveat:** inline script in `index.html` would break under the CSP, so T-021 moves it into `app/static/app.js` (mechanical, no behaviour change) and T-022 builds on that file.

**T-023 (S).** `POST /auth/change-password` (403 wrong current, 422 weak or same, bumps `session_version`, fresh cookie, clears lock) and `POST /users/{id}/reset-password` (admin, temporary password returned once, sets `must_change_password`, bumps version). Tests: `tests/test_password.py` (TC-1 to TC-6).

**T-022 (M).** Login, forced change, sign-out, role-based menu, user panel, change-password form, reset dialog in `app/static/app.js` and `index.html`. Starts on the spec contract with `GET /auth/me` and mocked-free local server; rebases as waves merge. Tests: `tests/test_frontend.py`, `tests/test_ui_browser.py` (browser tests follow ADR-0004). Finishes after T-020, T-021 and T-023.

## 4. API contract hand-offs

The contract is `spec.md` section 3. T-019 is the only ticket that may change `/auth/login`, `/auth/logout` or `/auth/me` shapes. If any ticket changes the contract, it updates `spec.md` in its own PR, tells the coordinator and a maintainer, and I flag the Artifacts for a human-reviewed Markdown PR. T-022 treats any contract change as a rebase trigger.

## 5. How parallel sessions split

One session per ticket, one branch, one PR. Wave 2 starts three sessions at once after T-019 merges; each session reads this file, the ticket and the spec, and never edits another ticket's files. Each session reports to the coordinator when its PR is up and when it merges. T-022 starts when the coordinator decides, with the spec contract as input.

## 6. PR, review and merge sequence

Per ticket: `feat/<N>-slug`, commits `<type>: <what> (#N)`, one PR into `develop` with `Closes #N`, run `pytest` first. After opening: subscribe to the PR, fix CI failures and actionable review findings, comment `@claude review again` after pushing fixes, at most 2 automated review rounds. If no blocking issue remains, add label `ready-for-merge`; otherwise (or for security, data-integrity or business-rule changes, which every ticket here touches) add `needs-human-review` and stop. I never merge; a maintainer merges. Order of merge: T-019 first, then wave 2 in any order, then T-022.

## 6b. Autonomy and stacking (2026-10-27)

After approval I run all tickets end to end without per-ticket confirmation. I stop only for a critical issue (security flaw, data loss, an unresolvable spec or contract contradiction, blocked access). Everything else goes into section 9 and is confirmed once at the end. Merges stay with a maintainer, so I do not wait on them: each dependent ticket's branch is stacked on its dependency's branch (T-020, T-021, T-023 on `feat/39-cookie-login`; T-022 on the latest of them) and the PR names its base. Wave 2 can run as separate parallel threads on the stacked branches if the coordinator starts them. The final report lists PRs, test results and section 9.

## 7. Risks

- T-019 is the bottleneck; it is held to the minimum above.
- Merge conflicts in `models.py`/`store.py`: mitigated by T-019's shared base and separate routers.
- The CSP change in T-021 can break the UI if any inline handler remains; the browser tests catch it.
- Seed admin variables must be set before first start on any deployed site (README and `.env.example`).
- Lockout is per username only (DDR-0001); noted, not solved here.

## 8. Questions for the maintainers (recommended option first)

1. Put the `must_change_password` gate in T-019's `current_user` (recommended, avoids a T-023 conflict) or in T-023? **Answered 2026-10-27: yes, T-019.**
2. Move the inline script to `app.js` in T-021 (recommended) or leave it to T-022? **Answered 2026-10-27: T-021.**
3. Mark ADR-0001 to ADR-0003 and DDR-0001 to DDR-0003 as Accepted in the T-019 PR (recommended) or leave them Proposed? **Answered 2026-10-27: Accepted.**

## 9. Issues & decisions (collected during implementation)

- T-019: login with AUTH_SECRET unset returns 503 (spec said only "refused").
- T-019 security scan, not changed: logout only clears the cookie and does not bump session_version (ADR-0002 accepts this ceiling; AC-5b needs logout to work without a session); a locked username answers 423 instead of 401, which reveals that the username exists (AC-3 and DDR-0001 require the distinct message). a maintainer to confirm both at the end.
- T-019 security scan, fixed: parallel login attempts could skip the lockout; check, verify and update now run under a per-username lock (a global lock was flagged as a login-DoS lever); per-IP rate limiting is not added.
- T-019 security scan, acknowledged: a login for an unknown username takes no per-user lock, so under heavy concurrency on a real username the two paths differ slightly in timing; the DoS finding on the earlier global lock pulls the other way. Per-IP rate limiting (DDR-0001 ceiling) is the real fix and is not in S-002.
- T-020: unlock is a PATCH with active true (no new route, contract unchanged). Admin-created accounts start with must_change_password false (the spec forces a change only for the seed admin and for reset).
- Branches are chained (feat/39 to feat/40 to feat/42 to feat/44) instead of each stacked on feat/39, to avoid test-fixture conflicts. Ticket numbers: T-021 is #42, T-022 #43, T-023 #44.
- T-021: the test client fixture is now an admin-signed-in client; anon_client and staff_client were added. The pre-existing browser tests (tests/test_ui_browser.py) were adapted (session cookie handed to the browser, revenue-token test replaced) but cannot run here (no playwright); CI or a maintainer should run them. The theme snippet moved to app/static/theme.js and the UI script to app/static/app.js for the CSP.
- T-021: until T-022, the web UI has no login screen, so it will show 401 errors when opened without a session.
- T-019 (small deviation, from the hosting review in PR #49): AUTH_SECRET must be at least 32 characters. Unset still only disables login; a shorter secret refuses login and stops startup. Added to T-019 (config check and test), not T-021.
- scripts/seed_admin.py (maintainer request): creates an admin or resets an existing user to admin, active and unlocked from a prompted password (12+ characters), straight in the database, so it works with existing users and needs no password in .env or shell history. The password was typed by the owner, so the account is not forced to change it. The server keeps users in memory, so it must be restarted afterwards. It does not go through the API, so there is no audit trail.
