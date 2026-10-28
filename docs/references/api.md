# API reference

Every HTTP endpoint of Clinic Booking, the session and role rules around it, and the business checks each one
applies. The code is the source of truth: `app/auth_routes.py`, `app/users.py`, `app/routes.py`. The rules behind
the checks are in `docs/business-rules.md`.

Run the app and open `/docs` for Swagger, which also lets you call the endpoints.

## Conventions

- Base URL `http://127.0.0.1:8000`. JSON in, JSON out. Dates are `YYYY-MM-DD`; times are ISO 8601 with an offset and
  are stored in UTC; money is integer cents.
- Errors are `{"detail": "<human sentence>"}`. The message is written for reception and shown to them unchanged.
- Deny by default: every endpoint needs a session except `POST /auth/login`, `POST /auth/logout`, `GET /health`,
  the docs pages and `/`. Unsafe requests (POST, PUT, PATCH, DELETE) from another origin are refused with `403`.
- A user who must change their password gets `403 Password change required` on everything except `/auth/me`,
  `/auth/change-password` and `/auth/logout`.

| Status | Meaning |
|---|---|
| `401` | No session, or a forged, expired or revoked one |
| `403` | Signed in but not allowed (wrong role, or a password change is pending) |
| `404` | The appointment, doctor, patient, holiday, time-off entry or user does not exist |
| `409` | Clashes with the current state: double booking, a forbidden status change, a closed day that still holds appointments, a duplicate, the last active admin |
| `422` | Bad input: timing rules, a backwards or year-long date range, an unknown status, a rejected body |
| `423` | The username is locked after five failed logins |
| `503` | `AUTH_SECRET` is missing or too short, so login is refused |

## Authentication

Sessions are a signed, `HttpOnly`, `SameSite=Strict` cookie (`clinic_session`, 8 hours). Login sets it, logout
clears it. Five failed logins lock the username for 15 minutes; a successful login or an admin re-enabling the
account clears the lock. Changing or resetting a password ends that user's other sessions.

| Method | Path | Who | Body / query | Returns |
|---|---|---|---|---|
| `POST` | `/auth/login` | anyone | `username`, `password` | `username`, `role`, `expires_at`, `must_change_password` |
| `POST` | `/auth/logout` | anyone | — | `204` |
| `GET` | `/auth/me` | session | — | the same session shape |
| `POST` | `/auth/change-password` | session | `current_password`, `new_password` (12+) | `204`, reissues the cookie |

## Users

Administrator-only. A user is `id`, `username`, `role` (`staff` or `admin`), `active`, `must_change_password`,
`created_at`; the password hash never leaves the server.

| Method | Path | Body / query | Notes |
|---|---|---|---|
| `GET` | `/users` | — | All users, by id |
| `POST` | `/users` | `username`, `password` (12+), `role` | `201`; `409` if the name is taken |
| `PATCH` | `/users/{id}` | `active`, `role`, both optional | Deactivating ends that user's sessions; `active: true` also unlocks; `409` would remove the last active admin |
| `POST` | `/users/{id}/reset-password` | — | Returns `temporary_password` once (`Cache-Control: no-store`); that user must change it at next sign-in |

## Doctors and patients

`GET /doctors` and `GET /patients` return the seed lists (`data/seed.json`) with `id`, `name`, and `fee_cents` or
`insured`. `GET /doctors/{doctor_id}/slots?date=YYYY-MM-DD` returns `doctor_id`, `date`, `slots` (free 30-minute
starts in UTC) and `closed` (the reason no booking is possible that day, or `null`).

## Appointments

| Method | Path | Body / query | Notes |
|---|---|---|---|
| `POST` | `/appointments` | `doctor_id`, `patient_id`, `start`, `duration_minutes` (`30` or `60`, default `30`) | `201` |
| `GET` | `/appointments` | `status`, `doctor_id`, `page` (default 1), `page_size` (default 10, max 100) | `{items, total, page, page_size}`, oldest start first |
| `GET` | `/appointments/today` | — | Appointments on today's clinic-local date |
| `GET` | `/appointments/{id}` | — | — |
| `POST` | `/appointments/{id}/check-in` | — | `scheduled` → `checked_in` |
| `POST` | `/appointments/{id}/complete` | — | `checked_in` → `completed` |
| `POST` | `/appointments/{id}/left-unseen` | — | `checked_in` → `left_unseen`, no fee |
| `POST` | `/appointments/{id}/no-show` | — | `scheduled` → `no_show`, only at or after the start time, 100% fee |
| `POST` | `/appointments/{id}/cancel` | — | `scheduled` → `cancelled`, only before the start time, free 24+ hours ahead else 50% |
| `POST` | `/appointments/{id}/reschedule` | `start`, `duration_minutes` (optional) | Same record; only while `scheduled` and before the start; no fee unless the length changes |
| `DELETE` | `/appointments/{id}` | — | Admin-only, `204` |

Lifecycle. No transition outside these is allowed (`409`):

```text
scheduled ──check-in──> checked_in ──complete────> completed
    │                        └──────left-unseen──> left_unseen
    ├──no-show (from the start time on)─────────> no_show
    └──cancel (before the start time)───────────> cancelled
```

Booking rules, all in clinic time (`CLINIC_TIMEZONE`, default `America/New_York`). A booking must be in the future,
within 60 days, on a weekday, on a 30-minute boundary, inside 08:00–17:00, and must not overlap 12:00–13:00.
Overlapping an active appointment for the same doctor or patient is `409`; so is booking a doctor's time off.
A holiday or a weekend is `422`. `GET /doctors/{id}/slots` already excludes all of these.

Fees are integer cents: consultation is the doctor's `fee_cents` per 30 minutes, at 80% for insured patients;
a late cancellation is 50% and a no-show 100% of it. See `app/fees.py`.

## Closures and time off

| Method | Path | Who | Body / query | Notes |
|---|---|---|---|---|
| `GET` | `/holidays` | session | — | Earliest first |
| `POST` | `/holidays` | admin | `date`, `name` | `201`; `409` if already a holiday or that day still has appointments |
| `DELETE` | `/holidays/{day}` | admin | — | `204` |
| `GET` | `/doctors/{doctor_id}/time-off` | session | — | Earliest first |
| `POST` | `/doctors/{doctor_id}/time-off` | admin | `start_date`, `end_date`, `reason` (optional) | `201`; both ends inclusive; `422` if backwards or over a year; `409` if those days still have that doctor's appointments |
| `DELETE` | `/doctors/{doctor_id}/time-off/{time_off_id}` | admin | — | `204` |

## Reports

`GET /reports/revenue?from=YYYY-MM-DD&to=YYYY-MM-DD` (admin-only, both ends inclusive, at most a year) returns
`from_date`, `to_date`, `totals`, `by_doctor` and `by_day`, each with `consultation_cents`, `penalty_cents` and
`total_cents`. Completed visits count as consultation revenue; no-show and cancellation fees as penalty revenue, on
the clinic-local date of the appointment's start. The web app shows it on the Revenue screen.

## Health

`GET /health` (public) returns `{"status": "ok", "timezone": "<CLINIC_TIMEZONE>"}`.
