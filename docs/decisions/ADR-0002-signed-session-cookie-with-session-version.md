# ADR-0002: Authenticate with a signed, stateless session cookie and a per-user session version

> Claude-assisted draft for Tung's edit. Decisions confirmed by Tung on 2026-10-27.

**Status:** Accepted  **Date:** 2026-10-27  **Deciders:** Tung  **Issue:** none yet (T-019, T-021)

## Context
The app has no user accounts; admin routes compare one shared `X-Admin-Token` (`app/routes.py:69`). The authentication feature (`plans/features/authentication/spec.md`) needs a login that lasts one shift, can be ended early, and works with the single-page frontend. Constraints: no new dependency without approval (`CLAUDE.md`), SQLite through the `store` layer, time through `clock.now_utc()`. ADR-0001 already decided that the credential lives in an `HttpOnly`, `SameSite=Strict` cookie, never in `localStorage`, behind a `script-src 'self'` CSP.

## Decision
We issue a session value signed with HMAC-SHA256 (standard library, key from `AUTH_SECRET`) carrying the user id, the user's `session_version` and an expiry 8 hours after login. It is set as the `clinic_session` cookie: `HttpOnly`, `SameSite=Strict`, `Secure` (on by default; `COOKIE_SECURE=false` for plain-http demos), `Path=/`, `Max-Age=28800`. There is no refresh. On every request we verify the signature and expiry, load the user, and require that the user is active and the stored `session_version` equals the one in the cookie. A password change, admin reset or disable increments `session_version`, which ends all older sessions; the user who just changed their password receives a fresh cookie. Logout clears the cookie. Unsafe methods (POST, PATCH, PUT, DELETE) are rejected with 403 when an `Origin` header is present and does not match the host; `SameSite=Strict` is the first layer and the API accepts JSON only. If `AUTH_SECRET` is empty, login is refused (fail closed).

## Options considered
| Option | Pros | Cons |
|---|---|---|
| **Signed stateless cookie + session version** (chosen) | No dependency; one user lookup per request, which we need anyway to check `active`; ends sessions on password change; works with same-origin `fetch`. | A copied cookie stays valid until expiry or a version bump; logout cannot revoke one cookie on its own. |
| Server-side session table | Revokes any single session instantly; list of devices. | New table and cleanup job; writes on login and logout; more code for a small app. |
| JWT with a library | Standard format. | New dependency needing approval; same revocation limits as the chosen option. |
| Bearer token in `localStorage` | Simple client code. | Any injected script can steal it; rejected in ADR-0001. |
| Refresh tokens | Tighter expiry. | Needs server-side storage; client chose 8 hours, no refresh. |

## Consequences
- Good: no dependency; safe defaults; one auth path for UI and API; tests can freeze the clock.
- Bad / ceiling: single-session revocation is not possible. Revisit with a session table if the clinic needs "sign out this device", an audit trail of sessions, or a shorter lifetime than a shift.
- Follow-up: T-019 (issue, verify, logout), T-021 (Origin check, CSP header, role dependency), T-023 (bump `session_version`); document `AUTH_SECRET` and `COOKIE_SECURE` in `.env.example` and `README.md`.
