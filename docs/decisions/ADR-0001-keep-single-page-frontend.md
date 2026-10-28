# ADR-0001: Keep the same-origin vanilla frontend; React (Vite) is the path when we outgrow it

> Claude-assisted; decisions confirmed by the maintainers on 2026-10-27.

**Status:** Accepted  **Date:** 2026-10-27  **Deciders:** Maintainers  **Issue:** none yet

## Context
A maintainer asked whether to split the frontend out into Next.js or React. What is true today:

- The whole UI is one file, `app/static/index.html` (~1,000 lines, inline CSS and vanilla JS, four hash-routed screens: Book, Appointments, Today, Revenue). FastAPI serves it at `/` and `/static` (`app/main.py:13-19`). Same origin, so there is no CORS config and no build step.
- All API calls go through one helper, `api()` (`app/static/index.html:572`). The only auth today is the shared `X-Admin-Token` header for admin routes (`app/routes.py:69`), typed by the user on the Revenue screen.
- Tests: Python only. `tests/test_frontend.py` checks served HTML and runs small JS checks under `node` when installed; `tests/test_ui_browser.py` is an optional Playwright smoke test against a live uvicorn. There is no JS toolchain, `package.json` or JS test runner in the repo.
- Constraints: no new dependencies without approval (`CLAUDE.md`); `REVIEW.md` forbids wildcard CORS and flags `innerHTML` with API data. The file has ~30 `innerHTML` uses, each relying on `esc()` being called correctly.
- Pending: the authentication feature (thread "Clarify a new client feature request") settled on staff and admin roles, username + password login, a short-lived signed token, and admin-managed users. That adds at least a login screen, a session state in the UI and a user-management screen.

## Decision
We keep the frontend as same-origin static files served by FastAPI and build the authentication UI in the existing `index.html`. We do not adopt Next.js. If the UI outgrows one file (signals below), we migrate to a React + TypeScript SPA built with Vite, whose `dist/` output FastAPI serves from the same origin, so the deployment, auth and security model stay as they are. That migration would be its own ticketed piece of work, done screen by screen after authentication ships, not during it.

Because the auth UI lands in a file that writes HTML with `innerHTML`, it ships with these guards (confirmed by a maintainer, 2026-10-27):
- The session token is never stored in `localStorage` or `sessionStorage`. It travels in an `HttpOnly`, `SameSite=Strict` cookie set by FastAPI, with a CSRF check on state-changing routes.
- FastAPI sends a `Content-Security-Policy` header with `script-src 'self'`, which blocks inline and third-party scripts. Both inline scripts move to static files: the theme script (`app/static/index.html:8`) stays a synchronous `<script src>` in `<head>` so the theme does not flash, and the main app script (`app/static/index.html:505`) moves too. The policy covers scripts only; the inline `<style>` block and `style=` attributes stay, so `style-src` allows `'unsafe-inline'` for now.
- Admin routes move off the `X-Admin-Token` header (`app/routes.py:69`) onto the same login session, so the UI has one auth path.
- New code sets text with `textContent`, and a test fails on any `innerHTML` assignment that interpolates a value not passed through `esc()`. A pattern test is easy to evade, so the CSP is the backstop, not the test.

## Options considered
| Option | Pros | Cons |
|---|---|---|
| **Stay as-is** (chosen for now) | Zero build step and zero new deps. One process, one origin, no CORS. Auth tokens stay simple (same-origin `fetch`). Existing Python tests keep working. | One large file gets harder to change as auth adds 2-3 screens. XSS safety depends on remembering `esc()` at every `innerHTML`. No component tests. |
| **React + Vite SPA, served by FastAPI** (path when we outgrow it) | Components, typed API client, JSX escapes output by default (removes the `innerHTML` class of bug). Still same origin: no CORS, same auth design. Vitest + Testing Library for component tests; Playwright test still applies. | Adds Node, npm and a build step to dev, CI and release. New dependency set to approve and keep patched. Rewrite of 4 screens plus the auth screens. Two test toolchains. |
| **React + Vite SPA, deployed separately** | Frontend can ship and scale on its own (CDN). | Cross-origin: needs an explicit CORS allowlist, and the token must travel in a header or a `SameSite=None` cookie with CSRF handling. Two deployments for a small training app. |
| **Next.js** | SSR/SSG, file routing, server actions, big ecosystem. | Needs a Node server (or a static export that drops most of its value). Its server becomes a second backend in front of FastAPI: auth must be proxied or duplicated (BFF cookie session), plus CORS or rewrites. Heaviest dependency and ops footprint. SSR and SEO bring nothing to a staff-only internal tool. |

## Consequences
- Good: the authentication feature is not blocked or coupled to a framework migration; security review stays on one origin and one auth path.
- Bad / ceiling: the single file keeps growing. Revisit and move to the React + Vite option when any of these hold: the file passes ~1,500 lines or 6 screens; two parallel tickets regularly conflict in `index.html`; an XSS finding comes from a missed `esc()`; or the team wants component-level tests. Re-check these signals when the auth screens land.
- Migration cost not to forget: React + Vite brings a large transitive npm dependency set. If we migrate, the new dependencies need approval per `CLAUDE.md`, the lockfile is committed, and `npm audit` (or an equivalent) runs in CI.
- Follow-up: link it from the authentication spec so the login UI is built in `index.html`. If the maintainers prefer to migrate, draft tickets for the React + Vite option (scaffold and build pipeline, typed API client, port screens one per ticket, auth screens, CI and release changes, retire the old file).

## Open questions for the maintainers
- Is there a driver beyond this app's size (team skills, a later patient-facing portal, a separate frontend team)? A patient portal with public pages would be the case where Next.js earns a second look.
- Would a Node toolchain in CI and release be acceptable if we later move to React + Vite?
