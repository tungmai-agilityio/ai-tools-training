# ADR-0004: Python Playwright runs the UI tests and captures screenshots, in CI on every PR

> Claude-assisted draft for maintainer edit. Nothing is installed or implemented by this record. Scope (E2E tests + screenshots in CI), the required-check rule and Chromium only confirmed by a maintainer on 2026-10-27.

**Status:** Accepted  **Date:** 2026-10-27  **Deciders:** Maintainers  **Issue:** none yet

## Context
A maintainer asked whether new screens and UI changes should come with screenshots, and whether to integrate Playwright. What is true today:

- Playwright is already in the project, in Python and optional. `requirements-dev.txt` pins `playwright>=1.45`, and `tests/test_ui_browser.py` has four smoke tests (booking flow, no sideways scroll on a phone for each screen, Revenue defaults, wrong admin token). They start uvicorn in a thread, freeze the browser clock (`page.clock.set_fixed_time`) and use a far-away browser timezone. They skip when Playwright or Chromium is missing, so plain `pytest` never runs them unless a developer set them up.
- `.mcp.json` registers the Playwright MCP server (`npx @playwright/mcp`), so Claude can drive a browser interactively. That is a dev aid, not a test suite.
- No CI runs `pytest`. `.github/workflows/` holds only `claude.yml` (the `@claude` bot) and `security.yml` (Claude security review). The suite being green is a local claim in each PR.
- The PR template already asks for "screenshots for UI changes" under Evidence, but nothing produces them, so they depend on someone remembering.
- The frontend stays one same-origin file with no build step and no Node toolchain (ADR-0001). The authentication feature (T-019 to T-023) adds a login screen, sign-out, role-based menus and a user-management panel; the session travels in an `HttpOnly`, `SameSite=Strict` cookie with a CSRF check, and the CSP becomes `script-src 'self'`.
- QA authors test cases in the feature's test-case Artifact; BA and QA review screens in the UI-design Artifact. Developers work from the repo.

## Decision
We keep Playwright for Python as the one browser tool and make it a real part of the suite:

1. **CI runs the whole suite on every PR to `develop`**, browser tests included, in Chromium only (a maintainer, 2026-10-27; add WebKit if reception uses iPads or Macs). In CI a missing browser fails the run instead of skipping (an env flag such as `REQUIRE_BROWSER=1`); locally the tests stay skippable so `pytest` works on a fresh clone. The job reports only for its first week; after a week with no flaky run it becomes a required check on `develop` (2026-10-27).
2. **Screenshots are a by-product of the browser tests**, not a separate tool. A small fixture saves named PNGs of each screen a test reaches, at desktop (1280x800) and phone (375x812) sizes, into `test-artifacts/screenshots/` (gitignored). CI uploads that folder as a workflow artifact kept for 14 days; the Artifact keeps the lasting "As built" copies. Screenshots are evidence for humans; tests never compare pixels. Screenshots show fake data only, and password and admin-token inputs are empty or masked (`mask=`) before capture, since CI artifacts can be downloaded by anyone who can see the repo.
3. **Where screenshots go:**
   - **PR:** the PR's Evidence section links the CI artifact and embeds the screens the change touches (the author or Claude adds them). PNGs are never committed to the repo.
   - **Artifacts:** for a new screen or a visible change, Claude uploads the PNGs to the feature's UI-design Artifact as an "As built" section next to the design, so BA and QA compare design and result in the place they already review.
4. **Determinism rules** for every browser test: the server clock and the browser clock frozen at the suite's fixed time; a fixed browser timezone away from New York; fixed viewports; fake data created through `tests/helpers` against an in-memory store; animations disabled for screenshots; web-first `expect()` assertions, never sleeps; tests never pass `bypass_csp`, and a CSP violation in the console fails the test; CI uses throwaway credentials set in the workflow (never repo secrets or `.env`).
5. **Login with cookies:** a fixture creates fake staff and admin users in the store and signs in through the real `POST /auth/login` with `context.request`, which shares its cookie jar with the page, so tests start signed in without touching the UI. One test per role signs in through the form itself. Tests never write a token into `localStorage` or inject the cookie by hand, so they exercise the same path the browser uses.

## Options considered
| Option | Pros | Cons |
|---|---|---|
| **No browser tests, manual screenshots** | Nothing to run or maintain. | Throws away the four tests we have. Screenshots stay forgotten or inconsistent (random data, random size, a dev's local timezone). Login, cookie, CSRF and CSP behaviour from the auth feature has no end-to-end check. |
| **Playwright for screenshots only** (a script, no assertions, no CI) | Cheap; gives PR evidence and Artifact images. | Pictures without assertions catch nothing; a broken screen is screenshotted happily. Still nothing runs the suite in CI. |
| **Python Playwright E2E + screenshots, in CI** (chosen) | Reuses what exists: `pytest`, the frozen clock, `store.reset()`, `tests/helpers`, the live-server fixture. One runner, one language, no `package.json`. Catches the auth risks unit tests can't (cookie actually sent, CSRF header on writes, CSP blocks inline script, staff can't see admin UI). Screenshots come out consistent and free. Adds the missing CI test run. | CI gets slower (Chromium download and launch, about 1-2 minutes; cacheable). Browser tests are the flakiest layer and need the rules above. A new workflow file to maintain. |
| **Node Playwright Test (`@playwright/test`)** | Best-in-class runner: HTML report, trace viewer, built-in retries, screenshot-on-failure, visual comparison. | Adds Node, `package.json`, a lockfile and a second test runner, which ADR-0001 deliberately avoids. Server start, seeding and the frozen clock would be rebuilt in JS. Tests for one feature would live in two languages. Worth revisiting only with the React + Vite migration, when Node arrives anyway. |
| **Visual regression (pixel baselines)** | Catches unintended visual changes. | Baselines churn with fonts, OS image and every intended change; review noise is high for a single-file UI under active change. Deferred. |

## Consequences
- Good: every PR proves `pytest` green in CI, not only locally. UI changes come with the same screenshots every time, which makes design review in the Artifact and PR review faster. The auth feature's cookie, CSRF and CSP guards get end-to-end tests.
- Bad / ceiling: CI minutes and a slower PR loop; browser tests need care to stay stable. Revisit if the browser job takes over ~5 minutes, a test is flaky more than once a month, or the React + Vite migration brings Node (then reconsider Node Playwright Test and visual comparison).
- Workflow:
  - `/plan-work`: for a UI ticket, the testing strategy names the screens and states to capture.
  - `/implement-ticket`: browser tests for the ticket's UI test cases are written first, like any other test; Verify runs them and produces the screenshots.
  - `/pr`: Evidence embeds the changed screens and links the CI artifact; Claude uploads the same PNGs to the feature's UI-design Artifact.
  - `/review-pr` and `REVIEW.md`: a UI change without screenshot evidence at both sizes is a nit; the reviewer compares the screenshots with the UI-design Artifact.
- Follow-up tickets (proposed, not created):
  1. Chore: CI workflow that runs `pytest` with Playwright Chromium on PRs to `develop`, caches the browser, fails when the browser is missing, and uploads screenshots.
  2. Chore: screenshot fixture and determinism helpers in `tests/` (both viewports, disabled animations, CSP-violation check), applied to the four existing browser tests.
  3. Docs: update `testing-conventions.md`, `REVIEW.md`, the PR template and the `plan-work`, `implement-ticket`, `pr` and `review-pr` skills as above.
  4. Auth (T-022): signed-in fixtures per role and browser tests for login, sign-out, role-based menu and CSRF, built on 1 and 2.
