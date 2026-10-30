# Deploy staging and production on Render (free)

> Claude-assisted draft; review and edit. Test use only, fake data only. See ADR-0005.

## Services
| Service | Branch | Purpose | Auto-deploy | `DEMO_SEED` |
|---|---|---|---|---|
| `clinic-booking-stag` | `develop` | staging and browser testing | on (every merge) | `1` |
| `clinic-booking` | `main` | production (releases, tagged `vX.Y.Z`) | off (`Deploy Production` only) | unset (off) |

Both are free web services. Staging redeploys from `develop` by itself; production redeploys only through the approval-gated workflow below. Production holds no demo data: only the admin is seeded from the secrets.

## One-time setup (done by a human)
1. Sign in to Render with GitHub, choose New > Blueprint and pick this repo. `render.yaml` defines both services: free plan, build and start commands, the `/health` check, auto-deploy (off for production) and the plain env vars; enter the three secrets below for each service when asked. (Manual alternative: New Web Service per branch, free instance type, copy the commands from `render.yaml`.)
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

## Production deploys (approval-gated)
Production does not deploy when `main` moves: `render.yaml` sets `autoDeploy: false` for `clinic-booking` (Render's current name is `autoDeployTrigger: off`). It deploys only from GitHub:

1. Actions → **Deploy Production** → Run workflow, with **Use workflow from: `main`**. The `production` environment only allows deployments from `main`, so a run started from another branch is refused. The workflow first appears on `main` after the release that adds it. Enter a tag on `main` (for example `v0.1.0`) or a commit SHA on `main`.
2. The deploy job targets the GitHub Environment `production`, so it stops at "Waiting for approval". The required reviewer is the maintainer. Self-review prevention is off while there is one reviewer, so the approval records the same person who started the run.
3. After approval the run calls the Render deploy hook with `ref=<commit>`, then polls production `/health` until it reports that commit (up to 20 minutes; the job times out at 30). It then requires `200` from both `/` and `/health`.
4. Read the result in the run summary: target commit, service URL, `main` tip and how far ahead it is, deploy id with a Render dashboard link, the `/` and `/health` codes. The service's Events tab shows the deploy itself. Check that the service URL is the production one: the workflow cannot tell staging and production apart if `APP_URL` is wrong.

A build that fails looks like a timeout in the run, not a status: this flow has no Render API to report one. When a run times out, open the Events tab for the failing deploy and dispatch again when it is fixed.

Names to create in GitHub → Settings → Environments → `production` (values never go in the repo):

| Name | Kind | Value |
|---|---|---|
| `RENDER_DEPLOY_HOOK_URL` | secret | the service's Deploy Hook from Render → Settings. It is a secret (the key is part of the URL): never print or commit it. Use **Regenerate Hook** in Render if it is exposed, then update it in **both** `production` and `production-rollback`. |
| `APP_URL` | variable | the service URL, `https://<service>.onrender.com`. |

The script never prints the hook URL; a failed call reports only the HTTP status. Keep the gate on the single job: an earlier job in the workflow would run before the approval. Deploys queue (`cancel-in-progress: false`); a third dispatch cancels the one still waiting for approval.

## Using it
- Open `https://<service>.onrender.com` (the URL is shown on the service in the dashboard). After 15 minutes idle the first load takes about a minute.
- Data resets on every restart, spin-down or redeploy, on both services (free plan, `DB_PATH=/tmp/clinic.db`). Startup reseeds the admin; staging also reseeds the demo appointments (`DEMO_SEED=1`, only while there are none). Production data is therefore not durable; see ADR-0005.
- Sign in with the seeded admin and change the password when asked (it resets with the data). There is no `ADMIN_TOKEN`.
- Every merge to `develop` redeploys staging; each production deploy wipes production's data too.
- `GET /health` returns `{"status", "timezone", "commit"}`. `commit` is Render's `RENDER_GIT_COMMIT` and is `null` locally or before the first deploy of this change. It proves the new code is serving, not that the store or the seeded admin works.

## If a merge does not deploy
**Staging:** open the service's Events tab and look for a deploy with trigger `commit`. If there is none, Render received no push event: check that the Render GitHub app is installed on the repo owner and has access to this repo (a service created from a public repo URL has no webhook), that Auto-Deploy is on for the right branch, then re-save the repo link under Settings > Build & Deploy. Use Manual Deploy meanwhile.

**Production:** a merge to `main` deploys nothing by design. Dispatch **Deploy Production** from `main` (above). The environment's branch policy refuses a run started from another branch.

## Rollback
Rolling back redeploys an earlier commit; it does not revert git history. Use it when a deploy is bad and a fix cannot wait.

1. Actions → **Rollback** → Run workflow, **Use workflow from: `develop`**, choose `production` or `staging`, and give a ref that was healthy: a release tag or commit on `main` for production, or a commit on `develop` for staging.
2. Production runs through the `production-rollback` environment, which has no required reviewer, so the job starts immediately; staging uses the `staging` environment (no reviewer). Only people with write access to the repo can start a run, and the summary names who did.
3. The run calls the deploy hook with that commit, polls `/health` until it reports it (up to 20 minutes; the job times out at 30), then requires `200` from `/` and `/health`. The summary names the restored commit and deploy ID with a dashboard link.
4. If the run fails, the site was not verified: redeploy the last good commit in Render from the Events tab, then revert the bad commit in a normal PR.

Rollback rebuilds from source; it is slower than reusing a Render build. Dispatching the commit that is already live reports "already live — nothing deployed (no-op)". A production rollback has its own queue, not the deploy one: Render runs one deploy at a time, so start it only when no deploy is running (a 202 from the hook times the run out after 20 minutes; re-run it once the deploy ends). A production rollback must target an ancestor of the live commit (read from `/health`); if the app is down the main tip is the bound, and the summary says so. Deploy Production takes only a `vX.Y.Z` tag or a full SHA, and needs a green `CI` run on that commit: re-run `CI` on `main` for a commit that has none. Data on the free plan resets on every deploy (ADR-0005).

Names to create: `production-rollback` — secret `RENDER_DEPLOY_HOOK_URL` (the production hook), variable `APP_URL` (the production URL), **no required reviewer**, branch policy `develop`. `staging` — its own `RENDER_DEPLOY_HOOK_URL` and `APP_URL`, no reviewer, branch policy `develop`. Values never go in the repo.

A staging rollback is temporary: the next merge to `develop` redeploys staging from its branch (staging keeps auto-deploy).

**Staging rehearsal:** pending — record the date, the two commits (A deployed, then B, then roll back to A), the duration and the outcome here after running it.

## Smoke test result (2026-10-28)
Service: `https://ai-tools-training.onrender.com/`. Passed: `/health` 200; `/` and static files over HTTPS; CSP header present; `/appointments` 401 without a session; wrong login 401; admin sign-in works; the seeded demo appointments are listed (a maintainer). Not yet verified: wake time after 15 minutes idle, and the data reset after a spin-down.
