# ADR-0005: Host the test site on Render's free tier, keep SQLite

**Status:** Accepted  **Date:** 2026-10-27  **Deciders:** Tung  **Issue:** TBD

> Claude-assisted draft, accepted by Tung on 2026-10-28.

## Context
We want a public HTTPS URL so Claude in Chrome can test the app. The app is one FastAPI process that serves `app/static/index.html` and keeps appointments in memory, written through to SQLite (`app/store.py`). Auth (ADR-0002, ADR-0003) uses a Secure/HttpOnly/SameSite=Strict cookie and a `script-src 'self'` CSP, so HTTPS and a single origin matter. ADR-0003 already retires `ADMIN_TOKEN` and seeds the first admin from `ADMIN_USERNAME` and `ADMIN_PASSWORD`. Data is fake and may reset.

## Decision
We deploy to a Render free web service from GitHub, with SQLite at `DB_PATH=/tmp/clinic.db`. The disk resets on restart, so each start reseeds the admin (ADR-0003 behaviour, from Render secrets) and, when `DEMO_SEED=1`, the demo data. No `ADMIN_TOKEN` is set. We do not move to Postgres.

## Options considered
| Option | Pros | Cons |
|---|---|---|
| Render free + SQLite (chosen) | No card, GitHub deploy, one long-lived process like local | Sleeps after 15 min idle (about 1 min to wake); 750 free hours a month; disk resets |
| Vercel Hobby | Free, FastAPI supported | Serverless: several instances break the in-memory store; only `/tmp` is writable (general knowledge, unconfirmed); deployment protection can block the browser |
| Postgres (any host) | Durable data | Rewrite `store.py`, new dependency, free DBs expire (Render: 30 days) |
| Cloud Run / Fly.io / Koyeb | Capable | Need a billing account or card; Fly has no free tier for new users |
| Cloudflare quick tunnel | No account, instant | URL changes each run, dies with the process; ad-hoc checks only |

Free-tier terms were checked on 2026-10-27 and change often; recheck at signup.

## Consequences
- Good: cheap, repeatable, matches local behaviour; no secrets in the repo.
- Bad / ceiling: cold starts and resets (the seeded admin must change the password after every reset). Revisit if we need several instances or data that survives restarts; then write an ADR on a persistent volume or Postgres.
- Follow-up: ticket T-028; deploy steps in `docs/deploy-render.md`; `render.yaml` in the repo root. Auth tickets T-019 to T-023 have landed.
