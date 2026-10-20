import json
from datetime import date
import sqlite3
import threading
from pathlib import Path

from app import config
from app.models import Appointment, Holiday, TimeOff, TimeOffIn

SEED_FILE = Path(__file__).resolve().parent.parent / "data" / "seed.json"

# Statuses that occupy the doctor's / patient's time.
ACTIVE_STATUSES = ("scheduled", "checked_in")


class Store:
    """Doctors and patients from data/seed.json; appointments, holidays and time off in memory, written through to SQLite."""

    def __init__(self, db_path=config.DB_PATH) -> None:
        data = json.loads(SEED_FILE.read_text())
        self.doctors = {d["id"]: d for d in data["doctors"]}
        self.patients = {p["id"]: p for p in data["patients"]}
        # ponytail: one shared connection + global write lock; fine for one uvicorn worker,
        # move to a connection per request (or a real DB) if multiple workers/processes write.
        self._lock = threading.Lock()
        self._db = sqlite3.connect(db_path, check_same_thread=False)
        self._db.execute("CREATE TABLE IF NOT EXISTS appointments (id INTEGER PRIMARY KEY, data TEXT NOT NULL)")
        rows = self._db.execute("SELECT data FROM appointments").fetchall()
        self.appointments: dict[int, Appointment] = {}
        for (data,) in rows:
            appt = Appointment.model_validate_json(data)
            self.appointments[appt.id] = appt
        self._next_id = max(self.appointments, default=0) + 1
        self._db.execute("CREATE TABLE IF NOT EXISTS holidays (day TEXT PRIMARY KEY, data TEXT NOT NULL)")
        self._db.execute("CREATE TABLE IF NOT EXISTS time_off (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT NOT NULL)")
        self.holidays = {h.date: h for h in (Holiday.model_validate_json(d) for (d,) in self._db.execute("SELECT data FROM holidays"))}
        self.time_off = {t.id: t for t in (TimeOff.model_validate_json(d) for (d,) in self._db.execute("SELECT data FROM time_off"))}

    def reset(self) -> None:
        with self._lock, self._db:
            self._db.execute("DELETE FROM appointments")
            self._db.execute("DELETE FROM holidays")
            self._db.execute("DELETE FROM time_off")
        self.appointments.clear()
        self.holidays.clear()
        self.time_off.clear()
        self._next_id = 1

    def save(self, appt: Appointment) -> None:
        with self._lock, self._db:
            self._db.execute("INSERT OR REPLACE INTO appointments (id, data) VALUES (?, ?)", (appt.id, appt.model_dump_json()))
        self.appointments[appt.id] = appt

    def delete(self, appointment_id: int) -> None:
        with self._lock, self._db:
            self._db.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
        self.appointments.pop(appointment_id, None)

    def save_holiday(self, holiday: Holiday) -> None:
        with self._lock, self._db:
            self._db.execute("INSERT INTO holidays (day, data) VALUES (?, ?)", (holiday.date.isoformat(), holiday.model_dump_json()))
        self.holidays[holiday.date] = holiday

    def delete_holiday(self, day: date) -> None:
        with self._lock, self._db:
            self._db.execute("DELETE FROM holidays WHERE day = ?", (day.isoformat(),))
        self.holidays.pop(day, None)

    def add_time_off(self, doctor_id: int, body: TimeOffIn) -> TimeOff:
        """SQLite assigns the id (AUTOINCREMENT: unique under concurrent requests, never reused after a delete)."""
        with self._lock, self._db:
            row_id = self._db.execute("INSERT INTO time_off (data) VALUES ('')").lastrowid
            entry = TimeOff(id=row_id, doctor_id=doctor_id, **body.model_dump())
            self._db.execute("UPDATE time_off SET data = ? WHERE id = ?", (entry.model_dump_json(), entry.id))
        self.time_off[entry.id] = entry
        return entry

    def delete_time_off(self, time_off_id: int) -> None:
        with self._lock, self._db:
            self._db.execute("DELETE FROM time_off WHERE id = ?", (time_off_id,))
        self.time_off.pop(time_off_id, None)

    def next_id(self) -> int:
        i = self._next_id
        self._next_id += 1
        return i

    def active_appointments(self) -> list[Appointment]:
        return [a for a in self.appointments.values() if a.status in ACTIVE_STATUSES]


store = Store()
