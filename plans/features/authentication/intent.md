# Intent: Authentication

**Requested by:** client (via a maintainer)  **Status:** Draft, Claude-assisted, awaiting human edit

## Problem
Anyone who can reach the API can book, check in, cancel and reschedule appointments and read patient data.
The only protection is one shared `X-Admin-Token` for a few admin endpoints. The clinic cannot tell who did what.

## Decisions from the client (clarified one question at a time)
| # | Question | Decision |
|---|---|---|
| 1 | Who logs in? | Staff and admins only. Patients stay unauthenticated. |
| 2 | How do they prove identity? | Username + password; the server sets a signed session in an `HttpOnly`, `SameSite=Strict` cookie. No token in `localStorage` or script-readable storage (confirmed by a maintainer, frontend ADR, PR #37). |
| 3 | What can each role do? | Staff: bookings and appointment lifecycle. Admin: everything staff can do, plus holidays, time off, delete, revenue report and user management. The shared admin token is retired. |
| 4 | How are accounts created? | Admins create, disable and reset staff accounts. The first admin is seeded from environment variables. |
| 5 | Session length? | 8-hour session cookie, no refresh. |
| 6 | Failed logins? | Lock the username for 15 minutes after 5 consecutive failures. |
| 7 | Password change and reset? | Signed-in users change their own password (current + new). Admins reset anyone's password and get a one-time temporary password; that user must change it at next login. No email. |
| 8 | Browser hardening? | A script-focused CSP (`script-src 'self'; object-src 'none'; base-uri 'self'`, no inline scripts) and admin routes moved off `X-Admin-Token` (confirmed by a maintainer, frontend ADR, PR #37). |
| 9 | Do read-only endpoints need login? | Yes. Only `/health`, `/`, `/static/*`, `/docs` and login are public. |
| 10 | Password rules? | 12 or more characters, no other rules; a new password must differ from the current one. |
| 11 | Cookie `Secure` flag? | On by default; `COOKIE_SECURE=false` overrides for plain-http demos. |
| 12 | Password change or reset and other sessions? | Ends the user's other sessions; the user who changed it stays signed in. |
| 13 | Who approved the rules? | The client (2026-10-27). Rules are in `docs/business-rules.md`. |
| 14 | Source of truth? | The repo Markdown. Artifacts are the BA/QA working draft; agreed changes reach the repo by a human-reviewed Markdown-only PR. |

## Out of scope
Patient accounts, doctor accounts, SSO/OAuth, refresh tokens, password reset by email, MFA, audit log UI.
