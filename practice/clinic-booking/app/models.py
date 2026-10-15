from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, field_validator

Status = Literal["scheduled", "checked_in", "completed", "cancelled", "no_show", "left_unseen"]


class AppointmentIn(BaseModel):
    doctor_id: int
    patient_id: int
    start: datetime
    duration_minutes: Literal[30, 60] = 30

    @field_validator("start")
    @classmethod
    def _require_timezone(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("start must include a timezone offset")
        return v.astimezone(timezone.utc)


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
