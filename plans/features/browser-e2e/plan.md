# Plan: Browser E2E tests and screenshots in CI (T-024 to T-027)

**Author:** Claude (draft, for maintainer edit)  **Status:** Implemented (T-024 to T-027 closed; approved 2026-10-27)  **Decisions:** ADR-0004 (Accepted)
One approval covers all four tickets: per-ticket `/plan-work` is skipped, each ticket's `## Plan` points here.

## Context
`develop` has the full auth feature but no workflow runs `pytest` (only `claude.yml`, `security.yml`). `tests/test_ui_browser.py` has 8 Playwright tests that skip when Chromium is missing, so they have probably never run in CI, and T-021 noted they were never run here either. ADR-0004 makes them a real CI job and adds desktop and phone screenshots.

## Findings that shape the plan
- `tests/test_ui_browser.py` already has the `base_url` (uvicorn thread), `page` fixtures and four T-022 UI tests (TC-1 to TC-4). The `page` fixture copies the TestClient admin cookie into the browser by hand; ADR-0004 wants a real `POST /auth/login` via `context.request`. T-027 replaces that.
- Session cookie is `Secure` by default (`COOKIE_SECURE`). Chromium accepts Secure cookies on `http://127.0.0.1`, but this is unverified; fallback is `COOKIE_SECURE=false` in the test server env only.
- Test config comes from `tests/conftest.py` (`AUTH_SECRET` setdefault). CI sets throwaway values in workflow `env`, no repo secrets.
- No `playwright` installed locally: I create a gitignored `.venv`, install `requirements-dev.txt` and `playwright install chromium` to run the tests before pushing.
- None of T-024..T-027 is in S-001/S-002. Approving this plan is taken as the scope decision; the `Sprint` field stays empty until you run `/sprint-prepare`.
- T-024..T-027 bodies have an empty "Summary / ACs / Test cases" section: I fill it (from the Done-when lists) before `/push-tickets`.

## Waves and dependencies
| Wave | Ticket | Branch | Needs | Files |
|---|---|---|---|---|
| 1 | T-025 snap helper, determinism, CSP check, `REQUIRE_BROWSER` | `feat/<N>-browser-screenshots` | nothing | `tests/test_ui_browser.py` (or `tests/browser/conftest.py`), `.gitignore` |
| 1 | T-024 CI workflow, pin Playwright | `feat/<N>-tests-workflow` | nothing in code; reads `REQUIRE_BROWSER` and the screenshot folder by name | `.github/workflows/tests.yml`, `requirements-dev.txt` |
| 2 | T-027 login fixtures and auth browser tests | `feat/<N>-browser-auth-tests` | T-025 (stacked on its branch) | `tests/test_ui_browser.py` |
| 2 | T-026 docs and skills | `feat/<N>-screenshot-docs` | describes T-024/T-025 behaviour; branched from `develop`, touches no code | `docs/references/testing-conventions.md`, `.claude/skills/{plan-work,implement-ticket,pr,review-pr}`, `.github/pull_request_template.md`, `REVIEW.md`, `README.md` |

Parallel: T-024 and T-025 touch disjoint files and run as two parallel agents; T-027 and T-026 likewise in wave 2. T-024's PR is the first to prove the whole job, so its CI run uses T-025's branch via a temporary merge locally only (no workflow trick). Merge order is yours; T-027 stacks on T-025 as in the auth feature (PR names its base).

## Per-ticket approach
**T-025.** `snap(page, name)` saves `test-artifacts/screenshots/<test>-<name>-{desktop,phone}.png` (resize to 1280x800 then 375x812, `animations="disabled"`, `mask=` on password and token inputs, restore size). Console listener fails the test on any CSP violation message; `bypass_csp` never used. `REQUIRE_BROWSER=1` turns `importorskip` and launch-failure skips into failures. Timezone `Asia/Ho_Chi_Minh`, `page.clock.set_fixed_time(FIXED_NOW)`, `store.reset()` already in place. Add `snap()` to the existing tests. Tests: "run twice, compare bytes" check done manually and noted in the PR; a test with an inline script page via `page.route` proving the CSP check fails; skip-vs-fail check for `REQUIRE_BROWSER`.

**T-024.** `tests.yml`: `pull_request` and `push` to `develop`, `permissions: contents: read`, Python version matching the repo, `pip install -r requirements-dev.txt`, cache `~/.cache/ms-playwright` keyed on the pinned Playwright version, `playwright install --with-deps chromium`, `REQUIRE_BROWSER=1`, throwaway `AUTH_SECRET` set in `env`, `pytest -q`, `upload-artifact` with `if: always()` and `retention-days: 14`. Actions pinned to commit SHAs (resolved with `gh api`, comment the tag). Playwright pinned to the latest exact version at implementation time.

**T-027.** `staff_page` and `admin_page` fixtures: `make_user` plus `context.request.post("/auth/login")`. One form-login test per role. Browser tests for the T-022 cases not yet covered (sign-out, CSRF missing or wrong on every state-changing method, cookie `HttpOnly` and `SameSite=Strict`, no credential in storage, user-management panel). Screenshots: login, signed-in header, user panel, passwords masked.

**T-026.** Edit the listed docs; one rule per file, others link to it. Docs only.

## Risks and mitigations
- Flaky browser layer: web-first `expect`, no sleeps, frozen clocks; the job reports only for a week before becoming required (your repo setting, not code).
- The 8 existing tests may fail on first real run (never run in CI): fixed inside T-025/T-027, not skipped or weakened.
- Supply chain: pinned SHAs and Playwright version, no `pull_request_target`, no secrets, `contents: read`.
- Screenshot leakage: fake data only, masked password fields, empty token fields; artifacts downloadable by repo readers.
- Secure cookie over http in CI: see findings.
- CI time target under 5 minutes warm: cache browser; measure in the T-024 PR.

## Execution rules (per your message)
Branches `feat/<N>-slug`, commits `<type>: <what> (#N)`, `code-reviewer` subagent locally before each PR, PR body with attribution block, then subscribe and follow the PR rules (max 2 review rounds, `ready-for-merge` or `needs-human-review`, never merge). Push to GitHub issues only after you authorise: I run `/push-tickets` dry run first and show it. Update the QA/test-cases Artifact and add "As built" screenshots when available. Remove worktrees and local branches at the end. Non-blocking questions are collected at the end.

## Verification
Local `.venv`: `REQUIRE_BROWSER=1 pytest -q` all green; plain `pytest` without Playwright skips browser tests; screenshots land in `test-artifacts/screenshots/` at both sizes and are identical on a second run; PR CI run shows the tests job and the downloadable artifact.

## Open assumptions (answer at the end, nothing blocks)
1. Scope: this approval stands in for sprint approval; Sprint field left empty.
2. T-027 stays a separate ticket (T-022 already merged) rather than folded into T-022.
3. Playwright pinned to the newest version available when T-024 is implemented.
