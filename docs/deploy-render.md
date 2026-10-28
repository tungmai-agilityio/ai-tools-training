# Deploy staging and production on Render (free)

> Claude-assisted draft; review and edit. Test use only, fake data only. See ADR-0005.

## Services
| Service | Branch | Purpose | `DEMO_SEED` |
|---|---|---|---|
| `clinic-booking-stag` | `develop` | staging and browser testing | `1` |
| `clinic-booking` | `main` | production (releases, tagged `vX.Y.Z`) | unset (off) |

Both are free web services with auto-deploy from their branch. Production holds no demo data: only the admin is seeded from the secrets.

## One-time setup (done by a human)
1. Sign in to Render with GitHub, choose New > Blueprint and pick this repo. `render.yaml` defines both services: free plan, build and start commands, the `/health` check, auto-deploy and the plain env vars; enter the three secrets below for each service when asked. (Manual alternative: New Web Service per branch, free instance type, copy the commands from `render.yaml`.)
2. Start command (Render terminates TLS at a proxy, hence `--proxy-headers`; the auth code sets `Secure` from config, not from the request scheme): `uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips='*'`
3. Environment variables (secrets in the dashboard only, never committed):

| Name | Value |
|---|---|
| `DB_PATH` | `/tmp/clinic.db` (in `render.yaml`) |
| `CLINIC_TIMEZONE` | `America/New_York` (in `render.yaml`) |
| `DEMO_SEED` | `1` on staging, absent on production (in `render.yaml`) |
| `AUTH_SECRET` | output of `openssl rand -hex 32`, at least 32 characters (secret; never reuse it elsewhere). Unset or short: the app refuses to start or refuses logins. |
| `ADMIN_USERNAME` | a throwaway username |
| `ADMIN_PASSWORD` | a throwaway password, 12+ characters (secret) |

## Using it
- Open `https://<service>.onrender.com` (the URL is shown on the service in the dashboard). After 15 minutes idle the first load takes about a minute.
- Data resets on every restart, spin-down or redeploy, on both services (free plan, `DB_PATH=/tmp/clinic.db`). Startup reseeds the admin; staging also reseeds the demo appointments (`DEMO_SEED=1`, only while there are none). Production data is therefore not durable; see ADR-0005.
- Sign in with the seeded admin and change the password when asked (it resets with the data). There is no `ADMIN_TOKEN`.
- Every merge to `develop` redeploys staging and every merge to `main` redeploys production; each wipes that service's data.

## If a merge does not deploy
Open the service's Events tab and look for a deploy with trigger `commit`. If there is none, Render received no push event: check that the Render GitHub app has access to this repo, that Auto-Deploy is on for the right branch, then re-save the repo link under Settings > Build & Deploy. Use Manual Deploy meanwhile.

## Smoke test result (2026-10-28)
Service: `https://ai-tools-training.onrender.com/`. Passed: `/health` 200; `/` and static files over HTTPS; CSP header present; `/appointments` 401 without a session; wrong login 401; admin sign-in works; the seeded demo appointments are listed (a maintainer). Not yet verified: wake time after 15 minutes idle, and the data reset after a spin-down.
