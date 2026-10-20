from datetime import date, datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Status = Literal["scheduled", "checked_in", "completed", "cancelled", "no_show", "left_unseen"]


def _aware_utc(v: datetime) -> datetime:
    if v.tzinfo is None:
        raise ValueError("start must include a timezone offset")
    return v.astimezone(timezone.utc)


class AppointmentIn(BaseModel):
    doctor_id: int
    patient_id: int
    start: datetime
    duration_minutes: Literal[30, 60] = 30

    _require_timezone = field_validator("start")(_aware_utc)


class RescheduleIn(BaseModel):
    start: datetime
    duration_minutes: Literal[30, 60] | None = None  # None keeps the current length

    _require_timezone = field_validator("start")(_aware_utc)


class Appointment(BaseModel):
    id: int
    doctor_id: int
    patient_id: int
    start: datetime  # always UTC
    duration_minutes: int
    status: Status = "scheduled"
    fee_cents: int
    cancellation_fee_cents: int = 0
    created_at: datetime


class Holiday(BaseModel):
    """A clinic-local day the whole clinic is closed."""

    date: date
    name: str = Field(min_length=1, max_length=100)


class TimeOffIn(BaseModel):
    """Whole clinic-local days, both ends inclusive."""

    start_date: date
    end_date: date
    reason: str = Field(default="", max_length=200)


class TimeOff(TimeOffIn):
    id: int
    doctor_id: int
