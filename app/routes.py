"""
API route definitions for the clinic booking system.

This module defines all HTTP endpoints for managing doctors, patients,
appointments, and appointment lifecycle actions (check-in, complete,
no-show, cancel). It reads and writes through the store and delegates
business logic to the scheduling, fees, and clock modules.
"""

import hmac
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Header, Query
from fastapi.responses import Response

from app import clock, config, fees, scheduling
from app.errors import DomainError
from app.models import Appointment, AppointmentIn, Holiday, RescheduleIn, Status, TimeOff, TimeOffIn
from app.store import store

router = APIRouter()

# Allowed state transitions for appointment lifecycle.
# Each key is a current status; the value is the set of statuses
# that an appointment may transition to from that state.
# Transitions not listed here (e.g. completed -> anything) are forbidden.
TRANSITIONS = {
    "scheduled": {"checked_in", "no_show", "cancelled"},
    "checked_in": {"completed", "left_unseen"},
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get(appointment_id: int) -> Appointment:
    """Look up an appointment by ID, raising a 404 DomainError if missing."""
    appt = store.appointments.get(appointment_id)
    if appt is None:
        raise DomainError("Appointment not found", 404)
    return appt


def _move(appt: Appointment, new_status: Status) -> None:
    """Transition an appointment to *new_status*, enforcing the TRANSITIONS map.

    Raises a 409 DomainError if the transition is not allowed from the
    appointment's current status.
    """
    if new_status not in TRANSITIONS.get(appt.status, set()):
        raise DomainError(f"Cannot go from {appt.status} to {new_status}", 409)
    appt.status = new_status


def _check_conflicts(doctor_id: int, patient_id: int, start: datetime, duration_minutes: int, ignore_id: int | None = None) -> None:
    """Reject if any active appointment (other than *ignore_id*) overlaps the same doctor or patient."""
    for other in store.active_appointments():
        if other.id == ignore_id:
            continue
        if not scheduling.overlaps(start, duration_minutes, other.start, other.duration_minutes):
            continue
        if other.doctor_id == doctor_id:
            raise DomainError("Doctor is not available at that time", 409)
        if other.patient_id == patient_id:
            raise DomainError("Patient already has an appointment at that time", 409)


def require_admin(x_admin_token: str | None = Header(default=None)) -> None:
    """Validate the admin token from the X-Admin-Token header.

    Raises a 403 DomainError if the provided token does not match.
    Fails closed: when ADMIN_TOKEN is empty/unset, every request is refused.
    """
    expected = config.ADMIN_TOKEN.encode()
    given = (x_admin_token or "").encode()
    if not expected or not hmac.compare_digest(given, expected):
        raise DomainError("Admin token required", 403)


# ---------------------------------------------------------------------------
# General endpoints
# ---------------------------------------------------------------------------

@router.get("/health")
def health():
    """Liveness / readiness probe returning the service status and configured timezone."""
    return {"status": "ok", "timezone": config.CLINIC_TIMEZONE}


@router.get("/doctors")
def list_doctors():
    """Return a list of all registered doctors."""
    return list(store.doctors.values())


@router.get("/patients")
def list_patients():
    """Return a list of all registered patients."""
    return list(store.patients.values())


# ---------------------------------------------------------------------------
# Doctor availability
# ---------------------------------------------------------------------------

@router.get("/doctors/{doctor_id}/slots")
def doctor_slots(doctor_id: int, day: date = Query(alias="date")):
    """Return available time slots for a given doctor on a specific date.

    Query parameter ``date`` is aliased from the ``day`` argument so clients
    use the more natural ``?date=2025-06-15`` syntax.
    """
    if doctor_id not in store.doctors:
        raise DomainError("Doctor not found", 404)
    return {
        "doctor_id": doctor_id,
        "date": day.isoformat(),
        "slots": [s.isoformat() for s in scheduling.free_slots(doctor_id, day)],
        "closed": scheduling.closed_reason(doctor_id, day),  # None on an open day
    }


# ---------------------------------------------------------------------------
# Clinic holidays and doctor time off (whole clinic-local days)
# ---------------------------------------------------------------------------

def _reject_if_booked(days: set[date], doctor_id: int | None = None) -> None:
    """Refuse to close days that still hold active appointments (for one doctor, or for anyone)."""
    clash = [
        a.id for a in store.active_appointments()
        if scheduling.to_local(a.start).date() in days and doctor_id in (None, a.doctor_id)
    ]
    if clash:
        raise DomainError(f"Reschedule or cancel appointments {sorted(clash)} first", 409)


@router.get("/holidays")
def list_holidays() -> list[Holiday]:
    """Return clinic holidays, earliest first."""
    return sorted(store.holidays.values(), key=lambda h: h.date)


@router.post("/holidays", status_code=201)
def add_holiday(body: Holiday, x_admin_token: str | None = Header(default=None)) -> Holiday:
    """Close the whole clinic on one day (admin-only)."""
    require_admin(x_admin_token)
    if body.date in store.holidays:
        raise DomainError("That day is already a holiday", 409)
    _reject_if_booked({body.date})
    store.save_holiday(body)
    return body


@router.delete("/holidays/{day}", status_code=204)
def remove_holiday(day: date, x_admin_token: str | None = Header(default=None)):
    """Reopen a holiday (admin-only)."""
    require_admin(x_admin_token)
    if day not in store.holidays:
        raise DomainError("Holiday not found", 404)
    store.delete_holiday(day)
    return Response(status_code=204)


@router.get("/doctors/{doctor_id}/time-off")
def list_time_off(doctor_id: int) -> list[TimeOff]:
    """Return a doctor's time off, earliest first."""
    if doctor_id not in store.doctors:
        raise DomainError("Doctor not found", 404)
    return sorted((t for t in store.time_off.values() if t.doctor_id == doctor_id), key=lambda t: (t.start_date, t.id))


@router.post("/doctors/{doctor_id}/time-off", status_code=201)
def add_time_off(doctor_id: int, body: TimeOffIn, x_admin_token: str | None = Header(default=None)) -> TimeOff:
    """Block whole days for one doctor, both ends inclusive (admin-only)."""
    require_admin(x_admin_token)
    if doctor_id not in store.doctors:
        raise DomainError("Doctor not found", 404)
    if body.end_date < body.start_date:
        raise DomainError("end_date must be on or after start_date", 422)
    if (body.end_date - body.start_date).days >= 366:
        raise DomainError("Time off cannot be longer than a year", 422)
    days = {body.start_date + timedelta(days=i) for i in range((body.end_date - body.start_date).days + 1)}
    _reject_if_booked(days, doctor_id)
    return store.add_time_off(doctor_id, body)


@router.delete("/doctors/{doctor_id}/time-off/{time_off_id}", status_code=204)
def remove_time_off(doctor_id: int, time_off_id: int, x_admin_token: str | None = Header(default=None)):
    """Cancel a doctor's time off (admin-only)."""
    require_admin(x_admin_token)
    entry = store.time_off.get(time_off_id)
    if entry is None or entry.doctor_id != doctor_id:
        raise DomainError("Time off not found", 404)
    store.delete_time_off(time_off_id)
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# Appointment CRUD
# ---------------------------------------------------------------------------

@router.post("/appointments", status_code=201)
def create_appointment(body: AppointmentIn) -> Appointment:
    """Create a new appointment after validating references, timing, and conflicts.

    Validation steps:
      1. Verify the referenced doctor and patient exist.
      2. Ensure the requested start time and duration are valid (not in the
         past, within business hours, etc.) via ``scheduling.validate_start``.
      3. Check for overlapping active appointments — a doctor cannot be
         double-booked, and a patient cannot have concurrent appointments.

    The consultation fee is calculated based on the doctor's base rate, the
    patient's insurance status, and the appointment duration.
    """
    doctor = store.doctors.get(body.doctor_id)
    patient = store.patients.get(body.patient_id)
    if doctor is None:
        raise DomainError("Doctor not found", 404)
    if patient is None:
        raise DomainError("Patient not found", 404)

    now = clock.now_utc()
    scheduling.validate_start(body.start, body.duration_minutes, now)
    scheduling.check_day_open(body.doctor_id, body.start)

    _check_conflicts(body.doctor_id, body.patient_id, body.start, body.duration_minutes)

    appt = Appointment(
        id=store.next_id(),
        doctor_id=body.doctor_id,
        patient_id=body.patient_id,
        start=body.start,
        duration_minutes=body.duration_minutes,
        # Fee is computed from doctor's base fee, patient insurance, and duration
        fee_cents=fees.consultation_fee(doctor["fee_cents"], patient["insured"], body.duration_minutes),
        created_at=now,
    )
    store.save(appt)
    return appt


@router.get("/appointments")
def list_appointments(
    status: Status | None = None,
    doctor_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    """List appointments with optional filters and cursor-based pagination.

    Supports filtering by ``status`` and/or ``doctor_id``.  Results are
    sorted by start time (then by ID for deterministic ordering) and
    paginated via ``page`` / ``page_size`` query parameters.
    """
    rows = sorted(store.appointments.values(), key=lambda a: (a.start, a.id))

    # Apply optional filters
    if status:
        rows = [a for a in rows if a.status == status]
    if doctor_id:
        rows = [a for a in rows if a.doctor_id == doctor_id]

    # Calculate pagination window
    offset = (page - 1) * page_size
    items = rows[offset: offset + page_size]
    return {"items": items, "total": len(rows), "page": page, "page_size": page_size}


@router.get("/appointments/today")
def todays_appointments():
    """Return all appointments whose clinic-local date is today.

    Uses the clinic's configured timezone (via ``scheduling.to_local``)
    to convert each appointment's UTC start time to a local date before
    comparing against today's date.
    """
    today = scheduling.to_local(clock.now_utc()).date()
    return [
        a
        for a in sorted(store.appointments.values(), key=lambda a: a.start)
        if scheduling.to_local(a.start).date() == today
    ]


@router.get("/appointments/{appointment_id}")
def get_appointment(appointment_id: int) -> Appointment:
    """Retrieve a single appointment by its ID."""
    return _get(appointment_id)


# ---------------------------------------------------------------------------
# Appointment lifecycle actions
# ---------------------------------------------------------------------------

@router.post("/appointments/{appointment_id}/check-in")
def check_in(appointment_id: int) -> Appointment:
    """Mark an appointment as checked-in (patient has arrived).

    Only valid from the ``scheduled`` status.
    """
    appt = _get(appointment_id)
    _move(appt, "checked_in")
    store.save(appt)
    return appt


@router.post("/appointments/{appointment_id}/complete")
def complete(appointment_id: int) -> Appointment:
    """Mark an appointment as completed (consultation finished).

    Only valid from the ``checked_in`` status.
    """
    appt = _get(appointment_id)
    _move(appt, "completed")
    store.save(appt)
    return appt


@router.post("/appointments/{appointment_id}/left-unseen")
def left_unseen(appointment_id: int) -> Appointment:
    """Mark a checked-in patient as having left before being seen. No fee.

    Only valid from the ``checked_in`` status.
    """
    appt = _get(appointment_id)
    _move(appt, "left_unseen")
    store.save(appt)
    return appt


@router.post("/appointments/{appointment_id}/no-show")
def no_show(appointment_id: int) -> Appointment:
    """Mark an appointment as a no-show and apply a no-show fee.

    Additional guard: the current time must be at or after the appointment's
    scheduled start — you cannot mark a patient as absent before the
    appointment was supposed to begin.
    """
    appt = _get(appointment_id)
    # Prevent premature no-show marking
    if clock.now_utc() < appt.start:
        raise DomainError("Cannot mark no-show before the appointment starts", 409)
    _move(appt, "no_show")
    # Apply the no-show penalty fee
    appt.cancellation_fee_cents = fees.no_show_fee(appt.fee_cents)
    store.save(appt)
    return appt


@router.post("/appointments/{appointment_id}/cancel")
def cancel(appointment_id: int) -> Appointment:
    """Cancel an appointment and apply a cancellation fee if applicable.

    Only valid from the ``scheduled`` status, and only before the start time.

    Fee logic:
      - If cancelled at least ``CANCEL_FREE_HOURS`` hours before the start
        time, no fee is charged (free cancellation window).
      - Otherwise, a late-cancellation fee is calculated and applied.
    """
    appt = _get(appointment_id)
    if appt.status == "cancelled":
        raise DomainError("Appointment is already cancelled", 409)
    if clock.now_utc() >= appt.start:
        raise DomainError("Cannot cancel after the start time; mark it as no-show or check the patient in", 409)
    # Before the fee calc, so a rejected cancel leaves the fee untouched
    _move(appt, "cancelled")

    # Determine how far in advance the cancellation is being made
    hours_left = (appt.start - clock.now_utc()).total_seconds() / 3600

    if hours_left >= config.CANCEL_FREE_HOURS:
        # Within the free cancellation window — no penalty
        appt.cancellation_fee_cents = 0
    else:
        # Late cancellation — charge the penalty fee
        appt.cancellation_fee_cents = fees.late_cancellation_fee(appt.fee_cents)
    store.save(appt)
    return appt


@router.post("/appointments/{appointment_id}/reschedule")
def reschedule(appointment_id: int, body: RescheduleIn) -> Appointment:
    """Move a scheduled appointment to a new time with the same doctor. No fee.

    Keeps the same record. Only valid from ``scheduled`` and before the
    current start time. The new slot gets the same checks as a new booking.
    """
    appt = _get(appointment_id)
    if appt.status != "scheduled":
        raise DomainError(f"Cannot reschedule a {appt.status} appointment", 409)
    now = clock.now_utc()
    if now >= appt.start:
        raise DomainError("Cannot reschedule after the start time", 409)
    duration = body.duration_minutes or appt.duration_minutes
    scheduling.validate_start(body.start, duration, now)
    scheduling.check_day_open(appt.doctor_id, body.start)
    _check_conflicts(appt.doctor_id, appt.patient_id, body.start, duration, ignore_id=appt.id)

    if duration != appt.duration_minutes:
        doctor = store.doctors[appt.doctor_id]
        patient = store.patients[appt.patient_id]
        appt.fee_cents = fees.consultation_fee(doctor["fee_cents"], patient["insured"], duration)
    appt.start = body.start
    appt.duration_minutes = duration
    store.save(appt)
    return appt


@router.delete("/appointments/{appointment_id}", status_code=204)
def delete_appointment(appointment_id: int, x_admin_token: str | None = Header(default=None)):
    """Permanently delete an appointment record (admin-only).

    Requires a valid admin token in the ``X-Admin-Token`` header.
    Returns HTTP 204 No Content on success.
    """
    require_admin(x_admin_token)
    # Verify the appointment exists before deleting
    _get(appointment_id)
    store.delete(appointment_id)
    return Response(status_code=204)
