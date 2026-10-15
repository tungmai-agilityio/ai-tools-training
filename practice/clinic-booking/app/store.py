import json
import sqlite3
import threading
from pathlib import Path

from app import config
from app.models import Appointment

SEED_FILE = Path(__file__).resolve().parent.parent / "data" / "seed.json"

# Statuses that occupy the doctor's / patient's time.
ACTIVE_STATUSES = ("scheduled", "checked_in")


class Store:
    """Doctors and patients from data/seed.json; appointments in memory, written through to SQLite."""

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

    def reset(self) -> None:
        with self._lock, self._db:
            self._db.execute("DELETE FROM appointments")
        self.appointments.clear()
        self._next_id = 1

    def save(self, appt: Appointment) -> None:
        with self._lock, self._db:
            self._db.execute("INSERT OR REPLACE INTO appointments (id, data) VALUES (?, ?)", (appt.id, appt.model_dump_json()))
        self.appointments[appt.id] = appt

    def delete(self, appointment_id: int) -> None:
        with self._lock, self._db:
            self._db.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
        self.appointments.pop(appointment_id, None)

    def next_id(self) -> int:
        i = self._next_id
        self._next_id += 1
        return i

    def active_appointments(self) -> list[Appointment]:
        return [a for a in self.appointments.values() if a.status in ACTIVE_STATUSES]


store = Store()
