"""Slot generation and booking validation. Business hours are in clinic time."""

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from app import config
from app.errors import DomainError
from app.store import store


def clinic_tz() -> ZoneInfo:
    return ZoneInfo(config.CLINIC_TIMEZONE)


def to_local(dt: datetime) -> datetime:
    return dt.astimezone(clinic_tz())


def overlaps(a_start: datetime, a_minutes: int, b_start: datetime, b_minutes: int) -> bool:
    """True if appointment A (the new one) collides with appointment B (existing)."""
    a_end = a_start + timedelta(minutes=a_minutes)
    return a_start <= b_start < a_end


def validate_start(start: datetime, duration_minutes: int, now: datetime) -> None:
    local = to_local(start)
    if start <= now:
        raise DomainError("Appointment must be in the future", 422)
    if start > now + timedelta(days=config.MAX_DAYS_AHEAD):
        raise DomainError(f"Cannot book more than {config.MAX_DAYS_AHEAD} days ahead", 422)
    if local.weekday() >= 5:
        raise DomainError("Clinic is closed on weekends", 422)
    if local.second or local.microsecond or local.minute % config.SLOT_MINUTES:
        raise DomainError("Start must be on a 30-minute boundary", 422)
    begin = local.hour * 60 + local.minute
    end = begin + duration_minutes
    if begin < config.WORK_START or end > config.WORK_END:
        raise DomainError("Outside working hours (08:00-17:00)", 422)
    if begin < config.LUNCH_END and end > config.LUNCH_START:
        raise DomainError("Overlaps the lunch break (12:00-13:00)", 422)


def free_slots(doctor_id: int, day: date) -> list[datetime]:
    """Free 30-minute slot starts (UTC) for a doctor on a clinic-local day."""
    tz = clinic_tz()
    if day.weekday() >= 5:
        return []
    busy = [a for a in store.active_appointments() if a.doctor_id == doctor_id]
    slots: list[datetime] = []
    minute = config.WORK_START
    while minute + config.SLOT_MINUTES <= config.WORK_END:
        in_lunch = config.LUNCH_START <= minute < config.LUNCH_END
        if not in_lunch:
            local = datetime.combine(day, time(minute // 60, minute % 60), tzinfo=tz)
            slot = local.astimezone(timezone.utc)
            if not any(overlaps(slot, config.SLOT_MINUTES, a.start, a.duration_minutes) for a in busy):
                slots.append(slot)
        minute += config.SLOT_MINUTES
    return slots
