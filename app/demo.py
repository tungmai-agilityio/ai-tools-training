"""Demo appointments for the hosted test site. Doctors and patients already come from data/seed.json."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app import clock
from app.models import AppointmentIn
from app.routes import create_appointment
from app.store import store

TZ = ZoneInfo("America/New_York")  # clinic time
TIMES = ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
         "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30"]


def next_weekday(after):
    d = after + timedelta(days=1)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def seed_demo_appointments() -> None:
    """Book Dr. Carter's next weekday through the booking route (same rules and fees); skip if any exist."""
    if store.appointments:
        return
    day = next_weekday(clock.now_utc().astimezone(TZ).date())
    for i, t in enumerate(TIMES):
        start = datetime.fromisoformat(f"{day}T{t}:00").replace(tzinfo=TZ)
        create_appointment(AppointmentIn(doctor_id=1, patient_id=1 + i % 3, start=start))
