"""Create demo appointments through the running API (needed to see pagination).

Usage:  DEMO_USERNAME=... DEMO_PASSWORD=... python scripts/seed_demo.py [base_url]     (default http://127.0.0.1:8000)

Logs in with an existing staff or admin account that has already changed its password.

Books 14 appointments for Dr. Carter on the next weekday, plus a couple for today
if it is still early enough. Appointments persist across restarts (SQLite).
"""
import os
import sys
from datetime import datetime
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.demo import TIMES, TZ, next_weekday  # noqa: E402

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"


def main() -> None:
    day = next_weekday(datetime.now(TZ).date())
    times = TIMES
    with httpx.Client(base_url=BASE, timeout=10) as c:
        login = c.post("/auth/login", json={"username": os.getenv("DEMO_USERNAME", ""), "password": os.getenv("DEMO_PASSWORD", "")})
        if login.status_code != 200 or login.json()["must_change_password"]:
            sys.exit(f"Login failed ({login.status_code}): set DEMO_USERNAME and DEMO_PASSWORD for an account that has changed its password.")
        # httpx will not send a Secure cookie over plain http, so pass the session cookie by hand.
        c.headers["Cookie"] = f"clinic_session={login.cookies.get('clinic_session')}"
        ok = 0
        for i, t in enumerate(times):
            start = datetime.fromisoformat(f"{day}T{t}:00").replace(tzinfo=TZ)
            r = c.post("/appointments", json={
                "doctor_id": 1, "patient_id": 1 + i % 3,
                "start": start.isoformat(), "duration_minutes": 30,
            })
            ok += r.status_code == 201
            if r.status_code != 201:
                print("skipped", t, r.status_code, r.text)
        print(f"Booked {ok}/{len(times)} appointments on {day}.")


if __name__ == "__main__":
    main()
