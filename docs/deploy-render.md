# Deploy the test site on Render (free)

> Claude-assisted draft; review and edit. Test use only, fake data only. See ADR-0005.

## One-time setup (done by a human)
1. Sign in to Render with GitHub and create a New Web Service from this repo, free instance type.
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Environment variables (dashboard only, never committed):

| Name | Value |
|---|---|
| `DB_PATH` | `/tmp/clinic.db` |
| `CLINIC_TIMEZONE` | `America/New_York` |
| `DEMO_SEED` | `1` |
| `AUTH_SECRET` | a random secret (secret) |
| `ADMIN_USERNAME` | a throwaway username |
| `ADMIN_PASSWORD` | a throwaway password, 12+ characters (secret) |

## Using it
- Open `https://<name>.onrender.com`. After 15 minutes idle the first load takes about a minute.
- Data resets on every restart or redeploy; startup reseeds the admin and demo data.
- Sign in with the seeded admin and change the password when asked (it resets with the data). There is no `ADMIN_TOKEN`.

## Not yet implemented
The admin seed and `AUTH_SECRET` come from the auth tickets (T-019, T-021); `DEMO_SEED` comes from ticket T-028. Until then the site needs `ADMIN_TOKEN` and a manual `python scripts/seed_demo.py`.
