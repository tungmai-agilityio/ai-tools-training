from datetime import date, datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, computed_field, field_validator

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


class RevenueTotals(BaseModel):
    consultation_cents: int = 0
    penalty_cents: int = 0

    @computed_field
    @property
    def total_cents(self) -> int:
        return self.consultation_cents + self.penalty_cents


class DoctorRevenue(RevenueTotals):
    doctor_id: int
    doctor_name: str


class DayRevenue(RevenueTotals):
    date: date


class RevenueReport(BaseModel):
    from_date: date
    to_date: date
    totals: RevenueTotals
    by_doctor: list[DoctorRevenue]
    by_day: list[DayRevenue]


Role = Literal["staff", "admin"]


class User(BaseModel):
    id: int
    username: str
    role: Role
    active: bool = True
    must_change_password: bool = False
    created_at: datetime


class UserRecord(User):
    """Stored user; never returned by the API (holds the password hash)."""

    password_hash: str
    failed_attempts: int = 0
    locked_until: datetime | None = None
    session_version: int = 0


class LoginIn(BaseModel):
    username: str = Field(max_length=100)
    password: str = Field(max_length=200)


class SessionOut(BaseModel):
    username: str
    role: Role
    expires_at: datetime
    must_change_password: bool


class UserCreateIn(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=12, max_length=200)  # config.MIN_PASSWORD_LENGTH
    role: Role

    @field_validator("username")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("username is required")
        return v


class UserPatchIn(BaseModel):
    active: bool | None = None
    role: Role | None = None


class ChangePasswordIn(BaseModel):
    current_password: str = Field(max_length=200)
    new_password: str = Field(min_length=12, max_length=200)  # config.MIN_PASSWORD_LENGTH


class ResetPasswordOut(BaseModel):
    temporary_password: str
