"""Create demo appointments through the running API (needed to see pagination).

Usage:  python scripts/seed_demo.py [base_url]     (default http://127.0.0.1:8000)

Books 14 appointments for Dr. Carter on the next weekday, plus a couple for today
if it is still early enough. Appointments persist across restarts (SQLite).
"""
import sys
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
TZ = ZoneInfo("America/New_York")  # clinic time


def next_weekday(after: date) -> date:
    d = after + timedelta(days=1)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def main() -> None:
    day = next_weekday(datetime.now(TZ).date())
    times = ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
             "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30"]
    with httpx.Client(base_url=BASE, timeout=10) as c:
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
