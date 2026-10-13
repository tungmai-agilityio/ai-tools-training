import json
from pathlib import Path

from app.models import Appointment

SEED_FILE = Path(__file__).resolve().parent.parent / "data" / "seed.json"

# Statuses that occupy the doctor's / patient's time.
ACTIVE_STATUSES = ("scheduled", "checked_in")


class Store:
    """In-memory data store, loaded from data/seed.json."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        data = json.loads(SEED_FILE.read_text())
        self.doctors = {d["id"]: d for d in data["doctors"]}
        self.patients = {p["id"]: p for p in data["patients"]}
        self.appointments: dict[int, Appointment] = {}
        self._next_id = 1

    def next_id(self) -> int:
        i = self._next_id
        self._next_id += 1
        return i

    def active_appointments(self) -> list[Appointment]:
        return [a for a in self.appointments.values() if a.status in ACTIVE_STATUSES]


store = Store()
