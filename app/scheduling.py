"""Slot generation and booking validation. Business hours are in clinic time."""

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from app import clock, config
from app.errors import DomainError
from app.models import DayRevenue, DoctorRevenue, RevenueReport, RevenueTotals
from app.store import store


def clinic_tz() -> ZoneInfo:
    return ZoneInfo(config.CLINIC_TIMEZONE)


def to_local(dt: datetime) -> datetime:
    return dt.astimezone(clinic_tz())


def overlaps(a_start: datetime, a_minutes: int, b_start: datetime, b_minutes: int) -> bool:
    """True if appointments A and B share any time. Back-to-back is not an overlap."""
    a_end = a_start + timedelta(minutes=a_minutes)
    b_end = b_start + timedelta(minutes=b_minutes)
    return a_start < b_end and b_start < a_end


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


DOCTOR_OFF = "Doctor is on time off that day"


def closed_reason(doctor_id: int, day: date) -> str | None:
    """Why the doctor takes no bookings on this clinic-local day, or None if the day is open."""
    if day.weekday() >= 5:
        return "Clinic is closed on weekends"
    holiday = store.holidays.get(day)
    if holiday:
        return f"Clinic is closed for {holiday.name}"
    if any(t.doctor_id == doctor_id and t.start_date <= day <= t.end_date for t in store.time_off.values()):
        return DOCTOR_OFF
    return None


def check_day_open(doctor_id: int, start: datetime) -> None:
    """Reject a start on a closed day: clinic closures are 422 like weekends, the doctor's time off is 409 like a clash."""
    reason = closed_reason(doctor_id, to_local(start).date())
    if reason:
        raise DomainError(reason, 409 if reason == DOCTOR_OFF else 422)


def free_slots(doctor_id: int, day: date) -> list[datetime]:
    """Free 30-minute slot starts (UTC) for a doctor on a clinic-local day. Slots that have started are not free."""
    tz = clinic_tz()
    now = clock.now_utc()
    if closed_reason(doctor_id, day):
        return []
    busy = [a for a in store.active_appointments() if a.doctor_id == doctor_id]
    slots: list[datetime] = []
    minute = config.WORK_START
    while minute + config.SLOT_MINUTES <= config.WORK_END:
        in_lunch = config.LUNCH_START <= minute < config.LUNCH_END
        if not in_lunch:
            local = datetime.combine(day, time(minute // 60, minute % 60), tzinfo=tz)
            slot = local.astimezone(timezone.utc)
            if slot > now and not any(overlaps(slot, config.SLOT_MINUTES, a.start, a.duration_minutes) for a in busy):
                slots.append(slot)
        minute += config.SLOT_MINUTES
    return slots


def build_revenue(appointments, doctors, from_date: date, to_date: date) -> RevenueReport:
    """Sum fees per doctor and per clinic day. Completed visits are consultation revenue; no-show and
    cancellation fees are penalty revenue. Each appointment counts on the clinic-local day of its start."""
    by_doctor = {d["id"]: DoctorRevenue(doctor_id=d["id"], doctor_name=d["name"]) for d in doctors.values()}
    by_day: dict[date, DayRevenue] = {}
    for a in appointments:
        day = to_local(a.start).date()
        if not from_date <= day <= to_date or a.status not in ("completed", "no_show", "cancelled"):
            continue
        consultation, penalty = (a.fee_cents, 0) if a.status == "completed" else (0, a.cancellation_fee_cents)
        if not consultation + penalty:
            continue
        # a stored appointment can outlive its doctor in the seed: keep its money under an 'Unknown' row
        doctor = by_doctor.setdefault(a.doctor_id, DoctorRevenue(doctor_id=a.doctor_id, doctor_name="Unknown doctor"))
        for row in (doctor, by_day.setdefault(day, DayRevenue(date=day))):
            row.consultation_cents += consultation
            row.penalty_cents += penalty
    return RevenueReport(
        from_date=from_date,
        to_date=to_date,
        totals=RevenueTotals(
            consultation_cents=sum(d.consultation_cents for d in by_doctor.values()),
            penalty_cents=sum(d.penalty_cents for d in by_doctor.values()),
        ),
        by_doctor=list(by_doctor.values()),
        by_day=[by_day[d] for d in sorted(by_day)],
    )
