# ADR-0003: Two roles, deny by default, and retire the shared admin token

> Claude-assisted draft for Tung's edit. Decisions confirmed by Tung on 2026-10-27.

**Status:** Proposed  **Date:** 2026-10-27  **Deciders:** Tung  **Issue:** none yet (T-020, T-021)

## Context
Today booking and lifecycle routes are open, while holidays, time off, delete and the revenue report each check `x_admin_token` themselves (`app/routes.py:145`, `:156`, `:182`, `:194`, `:418`) or use `require_admin` (`:435`). Patient names are readable through `GET /patients` and `GET /appointments`. The client chose staff and admins only, admin-managed accounts, and no shared token. Business rules are in `docs/business-rules.md`; failures raise `DomainError`, not `HTTPException`.

## Decision
We add two roles, `staff` and `admin`, stored on the user. Every route requires a valid session except `/health`, `/`, `/static/*`, `/docs` and `POST /auth/login`. Staff can use every booking, lifecycle and read route. Admins can also manage holidays, time off, delete appointments, read the revenue report and manage users. Protection is a FastAPI dependency (`current_user`, `require_role`) attached at the router level, so a new route is protected unless it is explicitly listed as public. `ADMIN_TOKEN` and the `X-Admin-Token` header are removed entirely, from code, config, docs, CI text and tests; `Authorization` headers are ignored. The first admin is seeded at startup from `ADMIN_USERNAME` and `ADMIN_PASSWORD`, only when the users table is empty. There is no default username or password in the repository, a seed password under 12 characters stops startup, and the seeded admin must change the password at first sign-in. If the seed settings are missing on an empty database the app still starts, warns, and nobody can log in. The settings are read once; changing them later does not alter an existing account. The last active admin cannot be disabled or demoted.

## Options considered
| Option | Pros | Cons |
|---|---|---|
| **Staff + admin, deny by default** (chosen) | Matches the existing admin split; patient data is no longer public; a forgotten decorator cannot leave a route open. | Every existing test needs a login helper. |
| Only admin routes need login | Smallest change. | Patient data and booking stay open to anyone. |
| Three roles (staff, doctor, admin) | Doctors see only their own patients. | Needs rules for doctor-patient scoping; not requested. |
| Keep `ADMIN_TOKEN` as a fallback | Easier migration. | Two auth paths; a shared secret nobody can attribute. |

## Consequences
- Good: one auth path, attributable actions, safe default for new routes.
- Bad / ceiling: the seed password sits in the deployment environment until the first sign-in, and an empty database with no seed settings is a locked app until they are set. No per-doctor or per-patient scoping. Revisit when doctors or patients need their own accounts.
- Follow-up: T-020 (user management), T-021 (router-level dependency, remove `ADMIN_TOKEN`, update `scripts/seed_demo.py` and tests), update the Admin section of `docs/business-rules.md`.
