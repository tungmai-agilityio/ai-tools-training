# Plan: Render free-tier test hosting

**Author:** Claude (draft, for maintainer edit)  **Status:** Draft, all questions answered, awaiting maintainer approval
Draft, Claude-assisted, human-edited. No code, no accounts, no deploy until a maintainer approves. Open questions are asked one at a time; answers are folded into section 7.

## 1. Context
Goal: a public HTTPS URL so Claude in Chrome (and humans) can test the app. Material: [ADR-0005](../../../docs/decisions/ADR-0005-render-free-tier-for-test-hosting.md) (Proposed), [docs/deploy-render.md](../../../docs/deploy-render.md), [T-028](../../tickets/T-028.md) (Draft). PR #49 with these drafts was merged 2026-10-27.

What changed since the drafts:
- **Auth has shipped** (T-019 to T-023, S-002 tickets closed). The "do not deploy until auth lands" blocker is gone. `AUTH_SECRET` fails closed (`app/auth.py`), `ADMIN_USERNAME`/`ADMIN_PASSWORD` seed the first admin at startup (`lifespan` -> `auth.seed_admin()`), `COOKIE_SECURE` defaults to true, `/health` exists.
- **`scripts/seed_demo.py` is an API client** that logs in with an account that already changed its password. T-028 AC-1 asks for startup seeding of the same data. Those are two different mechanisms (see risk R3).
- No `render.yaml` in the repo.

## 2. Decision to confirm
Accept ADR-0005: Render free web service, SQLite at `/tmp/clinic.db`, no Postgres, no `ADMIN_TOKEN`. Vercel, Cloud Run, Fly, Koyeb and Postgres stay rejected as written in the ADR. Recheck free-tier terms at signup (they change often).

## 3. Steps
1. **Docs (Claude):** set ADR-0005 to Accepted; update `docs/deploy-render.md` (drop the "do not deploy" banner, final env names).
2. **Code, T-028 (Claude):** startup `DEMO_SEED=1` seeding (doctors, patients, appointments; no login accounts; idempotent; fake data only). Reuse the data definitions from `scripts/seed_demo.py` rather than copy them.
3. **`render.yaml` (Claude, if approved):** a Blueprint with `runtime: python`, free plan, build `pip install -r requirements.txt`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips='*'`, `healthCheckPath: /health`, pinned `PYTHON_VERSION`, `autoDeploy` on `develop`, secrets declared `sync: false` (values entered by hand).
4. **Account and secrets (a maintainer, by hand):** see section 5.
5. **First deploy and smoke test (a maintainer + Claude in Chrome):** open URL, wait out the cold start, sign in as the seeded admin, change the password, book an appointment, confirm the `Secure` cookie and CSP in the browser. This is T-028 AC-5.
6. **CI/CD hook-up (deferred from the hooks plan):** deploy tier = Render test, auto-deploy on merge to `develop`, no production, no deploy MCP. Optional later: post-deploy `/health` smoke check in GitHub Actions. Not part of T-028.

## 4. Risks
| # | Risk | Mitigation |
|---|---|---|
| R1 | Free disk is ephemeral: every spin-down (15 min idle), restart and redeploy wipes `/tmp/clinic.db`. Changed admin password, bookings and any users Claude in Chrome created are lost. | Accepted by ADR-0005. Startup reseeds admin and demo data; document that tests must not depend on state surviving idle time. Revisit only if we need durable data (persistent disk = paid). |
| R2 | Cold start of about a minute makes the first browser step time out. | Smoke test waits and polls `/health` first; note in the doc. |
| R3 | Seeding mismatch: `seed_demo.py` needs a changed-password account and a running server; `DEMO_SEED` seeds before any login exists. | Seed through the `store` layer in `lifespan`, sharing data definitions with the script. Decide in T-028 planning. |
| R4 | Behind Render's TLS proxy the app sees http; `Secure` cookie, Origin/Host checks on unsafe methods and the CSP could misbehave. | `--proxy-headers` flag; cookie `Secure` comes from config, not request scheme; verify in the smoke test. |
| R5 | Public URL with a seeded admin: weak password gets guessed. | 12+ character throwaway password, lockout exists (DDR-0001), URL not shared, fake data only. |
| R6 | Stale session cookie after a reset (signed with the same `AUTH_SECRET`, user gone). | Verify the app rejects it cleanly and returns to the login screen; add a test if not. |
| R7 | Free-tier terms or 750 h/month change. | Recheck at signup; ADR lists fallbacks. |

## 5. What a maintainer must do by hand
- Create or sign in to a Render account with GitHub (no card needed on the free plan) and grant Render read access to `tungmai-agilityio/ai-tools-training` only.
- Create the Web Service (or apply the Blueprint) on the free instance type.
- Enter secrets in the Render dashboard, never in the repo or chat: `AUTH_SECRET` (`openssl rand -hex 32`), `ADMIN_USERNAME`, `ADMIN_PASSWORD` (12+ chars, throwaway). Plain values: `DB_PATH=/tmp/clinic.db`, `CLINIC_TIMEZONE=America/New_York`, `DEMO_SEED=1`.
- Sign in once and change the admin password.
- Approve each push and merge as usual (CLAUDE.md).

## 6. Tickets
| Ticket | Action |
|---|---|
| T-028 Deploy a free test site on Render | Exists (Draft). Update: drop auth dependency (landed), add `render.yaml` if approved, clarify AC-1 vs seed script (R3), put in a sprint. |
| Optional: post-deploy smoke check in CI | New chore, only after T-028 works. Not created yet. |

No other tickets. Nothing is created in GitHub until a maintainer says so.

## 7. Open questions (asked one at a time; recommended option first)
1. ~~Accept ADR-0005 (Render, SQLite, no Postgres)?~~ **Answered 2026-10-28: yes.** The ADR file is set to Accepted when the plan is approved.
2. ~~Add `render.yaml` to T-028 scope?~~ **Answered 2026-10-28: yes.**
3. ~~Which sprint does T-028 belong to?~~ **Answered 2026-10-28: add it to S-002** (scope change; needs team agreement per CLAUDE.md, a maintainer to confirm with the team before `/sprint-prepare` edits S-002).
4. ~~Auto-deploy on every merge to `develop`, or manual?~~ **Answered 2026-10-28: auto-deploy.**
5. ~~Seed approach for `DEMO_SEED` (R3)?~~ **Answered 2026-10-28: startup via `store`, sharing data definitions with the script.**

No open questions remain. Status: ready for maintainer approval.

## Verification (after approval)
`make test`, `make lint`; then the manual smoke test in step 5 over HTTPS from Claude in Chrome.
