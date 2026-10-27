# Spec: Authentication (T-019 to T-023)

**Author:** Claude (draft, for Tung to edit)  **Status:** Approved  **PRD:** `plans/features/authentication/intent.md`  **Artifacts:** [spec and test cases](https://claude.ai/artifact/Vx4CrGK2SRXTmfFyVShedS), [UI design](https://claude.ai/artifact/VaAYYy7WoVCPzw2wEwS6jp)  **Last updated:** 2026-10-27

**Decisions:** [ADR-0001](../../../docs/decisions/ADR-0001-keep-single-page-frontend.md), [ADR-0002](../../../docs/decisions/ADR-0002-signed-session-cookie-with-session-version.md), [ADR-0003](../../../docs/decisions/ADR-0003-two-roles-deny-by-default-and-retire-admin-token.md), [DDR-0001](../../../docs/decisions/DDR-0001-lock-account-after-five-failed-logins.md), [DDR-0002](../../../docs/decisions/DDR-0002-password-rules-change-and-admin-reset.md), [DDR-0003](../../../docs/decisions/DDR-0003-signed-in-experience-by-role.md)

> A Spec says **how**. It must be reviewable before any code is written.

## 1. Context
Admin endpoints use one shared token compared in `require_admin` (`app/routes.py:69`); `add_holiday`, `remove_holiday`,
`add_time_off`, `remove_time_off` and `delete_appointment` each take `x_admin_token` directly, and the revenue report
uses `Depends(require_admin)` (`app/routes.py:435`). Booking and lifecycle endpoints are open. There are no user accounts.
This feature adds staff/admin accounts, login with a signed session cookie, role checks on every protected endpoint, and a login UI.
No new dependency: hashing and signing use the standard library (`hashlib.scrypt` or PBKDF2, `hmac`).

## 2. Proposed design
- **`app/config.py`:** add `AUTH_SECRET` (session signing key; empty means login is refused, fail closed), `ADMIN_USERNAME`,
  `ADMIN_PASSWORD` (seed the first admin if no users exist), `SESSION_TTL_HOURS = 8`, `SESSION_COOKIE = "clinic_session"`,
  `COOKIE_SECURE` (default true; `false` only for plain-http local dev), `LOCKOUT_FAILURES = 5`, `LOCKOUT_MINUTES = 15`.
- **`app/auth.py` (new):** `hash_password`, `verify_password` (constant time), `issue_session(user)` (signed value carrying user id, `session_version` and expiry), `read_session(value)`,
  `set_session_cookie` / `clear_session_cookie`, dependencies `current_user` and `require_role("staff" | "admin")`, and a CSRF check (below). Time comes from `clock.now_utc()` through the module.
- **`app/store.py`:** a `users` table (SQLite, existing store layer): id, username (unique, case-insensitive), password_hash,
  role, active, failed_attempts, locked_until (UTC), must_change_password, session_version, created_at.
- **`app/models.py`:** `UserIn`, `User` (never includes the hash), `LoginIn`, `SessionOut`, `ChangePasswordIn`, `ResetPasswordOut`.
- **`app/routes.py`:** `POST /auth/login`, `GET /auth/me`, user-management routes, and role dependencies replacing the
  `x_admin_token` checks. Lifecycle changes still go through `routes._move()`; failures raise `DomainError`.
- **`app/main.py`:** middleware that adds the CSP header `Content-Security-Policy: script-src 'self'; object-src 'none'; base-uri 'self'` to every response and rejects unsafe requests (POST, PATCH, PUT, DELETE) whose `Origin` header is present and does not match the host.
- **`app/static/index.html` and `app/static/app.js` (new):** the UI script moves out of the HTML so inline scripts can be refused. Login screen, sign-out, admin user-management panel. The UI stores no credential anywhere: the browser sends the cookie by itself and the UI learns who is signed in from `GET /auth/me`.
  Draft UI design: https://claude.ai/artifact/VaAYYy7WoVCPzw2wEwS6jp (private; Tung to edit).

## 3. API changes
| Method | Path | Role | Request | Response | Errors |
|---|---|---|---|---|---|
| POST | `/auth/login` | public | `{username, password}` | `200 {username, role, expires_at, must_change_password}` and `Set-Cookie: clinic_session=...; HttpOnly; SameSite=Strict; Secure; Path=/; Max-Age=28800`. No credential in the body. | `401` generic, `423` locked, `422` |
| POST | `/auth/logout` | any | none | `204` and the cookie is cleared (`Max-Age=0`) | none (idempotent) |
| GET | `/auth/me` | any | none | `200 {username, role, expires_at, must_change_password}` | `401` |
| GET | `/users` | admin | none | `200 [User]` | `401`, `403` |
| POST | `/users` | admin | `{username, password, role}` | `201 User` | `409` duplicate, `422` weak password |
| PATCH | `/users/{id}` | admin | `{active?, role?}` | `200 User` | `404`, `409` last active admin |
| POST | `/users/{id}/reset-password` | admin | none | `200 {temporary_password}` shown once | `404` |
| POST | `/auth/change-password` | any | `{current_password, new_password}` | `204` | `401`, `403` wrong current password, `422` weak or same as current |
| existing booking/lifecycle/read routes | | staff or admin | unchanged | unchanged | `401` no/expired session, `403` bad Origin on unsafe methods |
| holidays, time off, delete appointment, revenue report | | admin | unchanged | unchanged | `401`, `403` staff |
Public: `/health`, `/`, `/static/*`, `/docs`, `POST /auth/login`. Credential: the session cookie only; `Authorization` and `X-Admin-Token` headers are ignored.

## 4. Data model / persistence
New `users` table, created on startup by the store layer; no change to appointments. Existing `data/clinic.db` keeps working.
The first admin is seeded only when the table is empty and both env vars are set. The password must have 12+ characters (otherwise startup stops with an error) and the account starts with `must_change_password` true. With the table empty and a variable unset, the app starts, logs a warning and nobody can log in. After seeding, changing the env vars has no effect. There is no default username or password in the repository.

## 5. Business rules applied (approved by Tung as client, 2026-10-27; recorded in `docs/business-rules.md`)
- Only staff and admins can use the clinic API, including every read; patients have no accounts. Public: `/health`, `/`, `/static/*`, `/docs`, login.
- A password has at least 12 characters, with no other rules.
- The first administrator is created at first start from deployment settings (proposed, awaiting Tung's confirmation): there is no default password, and that administrator must change the password at first sign-in.
- Staff can book, check in, complete, mark left-unseen or no-show, cancel and reschedule. Admins can do all of that plus holidays, time off, deleting appointments, the revenue report and user management.
- A login session is valid for 8 hours and cannot be refreshed. It lives only in an `HttpOnly`, `SameSite=Strict` cookie; scripts can never read it.
- After 5 consecutive failed logins a username is locked for 15 minutes; a successful login resets the count.
- Signed-in users can change their own password by giving the current one; the new one follows the same rules as a new account and must differ from the current one.
- An admin can reset a user's password; the system returns a temporary password once. The user must change it at next login and can do nothing else until then.
- A password change or reset clears the lockout and ends the user's other sessions.
- An admin can disable an account; a disabled account's session stops working at once.
- The last active admin cannot be disabled or demoted.

## 6. Alternatives considered
| Option | Pros | Cons | Why not |
|---|---|---|---|
| Per-user API keys | simplest | no login screen, no expiry | client chose username + password |
| Refresh tokens | tighter expiry | needs server-side token storage | client chose 8 h, no refresh |
| Bearer token in `localStorage` or `sessionStorage` | simple client code | any injected script can steal it | Tung chose an `HttpOnly` cookie (frontend ADR, PR #37) |
| JWT library | standard format | new dependency needs approval | stdlib HMAC is enough |

## 7. Edge cases
- Unknown username and wrong password return the same `401` and take similar time (no user enumeration).
- Locked account stays locked even with the right password until `locked_until` passes (frozen clock in tests).
- Session expiry exactly at 8 h, tampered signature, session for a deleted or disabled user, `AUTH_SECRET` unset.
- Cookie attributes on login and on logout; logging out twice; logging in again replaces an existing cookie.
- Cross-site POST with a foreign `Origin`; same-site request without `Origin` (allowed); `Origin` with a different port.
- Username case ("Nurse" vs "nurse"), leading/trailing spaces, very long input.
- Two admins disable each other at the same time (last-admin guard).

## 8. Security and privacy
Passwords never stored or logged in clear; hash is salted and never returned. Fixed-time comparisons. Secrets only from
env, never committed (fake data only; `.env.example` gets placeholders). The cookie is `HttpOnly`, `SameSite=Strict` and `Secure`, so it is not readable by scripts and is not sent on cross-site requests.

**CSRF.** `SameSite=Strict` is the first defence; the `Origin` check on unsafe methods is the second, and the API accepts JSON bodies only. No CSRF token is needed on top of these (revisit if a cross-site embed is ever required).

**CSP.** `script-src 'self'` stops inline and third-party scripts, which limits XSS that could act with the cookie; `object-src 'none'` and `base-uri 'self'` close plugin and base-tag injection. Inline `<script>` and inline event handlers in `index.html` must move to `app.js`; inline styles are unaffected because the policy does not restrict styles, images or connections (decided by Tung).

**Logout and expiry.** Logout clears the cookie. Because the session is signed and stateless, a copied cookie stays valid until it expires unless the user's `session_version` changes; a password change, reset or disable bumps it, which ends every older session of that user.
Rate limiting beyond the per-username lockout is out of scope.

## 9. Test plan
| Test | File | Covers |
|---|---|---|
| password hash/verify, session round trip, expiry, tamper | `tests/test_auth.py` | T-019 |
| cookie attributes, no credential in body, logout clears cookie | `tests/test_login.py` | T-019 |
| change password (right/wrong current, weak, forced change gate) | `tests/test_password.py` | T-023 |
| login success, generic 401, lockout, reset on success | `tests/test_login.py` | T-019 |
| admin creates/disables users, last-admin guard | `tests/test_users.py` | T-020 |
| every route: no session 401, staff 403 on admin routes, foreign Origin 403, CSP header present | `tests/test_authorization.py` | T-021 |
| login form, sign-out, role-based menu | `tests/test_frontend.py`, `tests/test_ui_browser.py` | T-022 |
Existing tests get a helper that logs in; none are weakened.

## 10. Rollout
Add `AUTH_SECRET`, `ADMIN_USERNAME`, `ADMIN_PASSWORD` to `.env.example` and README. `ADMIN_TOKEN` and `X-Admin-Token` are removed entirely
in T-021 (code, config, README, `CLAUDE.md`, `REVIEW.md`, CI text, docs and tests); `scripts/seed_demo.py` must log in. Deploy note: set the three variables before first start.

## 11. Open questions
None. Resolved by Tung on 2026-10-27: reads need login; passwords are 12+ characters; CSP is `script-src 'self'; object-src 'none'; base-uri 'self'`; `Secure` cookie by default with `COOKIE_SECURE` override; password change or reset ends other sessions; rules approved as client; the repo Markdown stays the source of truth.
