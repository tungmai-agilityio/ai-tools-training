from datetime import date

from fastapi import APIRouter, Header, Query
from fastapi.responses import Response

from app import clock, config, fees, scheduling
from app.errors import DomainError
from app.models import Appointment, AppointmentIn, Status
from app.store import store

router = APIRouter()

# status -> statuses it may move to via the check-in / complete / no-show actions
TRANSITIONS = {
    "scheduled": {"checked_in", "no_show", "cancelled"},
    "checked_in": {"completed"},
}


def _get(appointment_id: int) -> Appointment:
    appt = store.appointments.get(appointment_id)
    if appt is None:
        raise DomainError("Appointment not found", 404)
    return appt


def _move(appt: Appointment, new_status: Status) -> None:
    if new_status not in TRANSITIONS.get(appt.status, set()):
        raise DomainError(f"Cannot go from {appt.status} to {new_status}", 409)
    appt.status = new_status


def require_admin(x_admin_token: str | None = Header(default=None)) -> None:
    if config.ADMIN_TOKEN and x_admin_token != config.ADMIN_TOKEN:
        raise DomainError("Admin token required", 403)


@router.get("/health")
def health():
    return {"status": "ok", "timezone": config.CLINIC_TIMEZONE}


@router.get("/doctors")
def list_doctors():
    return list(store.doctors.values())


@router.get("/patients")
def list_patients():
    return list(store.patients.values())


@router.get("/doctors/{doctor_id}/slots")
def doctor_slots(doctor_id: int, day: date = Query(alias="date")):
    if doctor_id not in store.doctors:
        raise DomainError("Doctor not found", 404)
    return {
        "doctor_id": doctor_id,
        "date": day.isoformat(),
        "slots": [s.isoformat() for s in scheduling.free_slots(doctor_id, day)],
    }


@router.post("/appointments", status_code=201)
def create_appointment(body: AppointmentIn) -> Appointment:
    doctor = store.doctors.get(body.doctor_id)
    patient = store.patients.get(body.patient_id)
    if doctor is None:
        raise DomainError("Doctor not found", 404)
    if patient is None:
        raise DomainError("Patient not found", 404)

    now = clock.now_utc()
    scheduling.validate_start(body.start, body.duration_minutes, now)

    for other in store.active_appointments():
        if not scheduling.overlaps(body.start, body.duration_minutes, other.start, other.duration_minutes):
            continue
        if other.doctor_id == body.doctor_id:
            raise DomainError("Doctor is not available at that time", 409)
        if other.patient_id == body.patient_id:
            raise DomainError("Patient already has an appointment at that time", 409)

    appt = Appointment(
        id=store.next_id(),
        doctor_id=body.doctor_id,
        patient_id=body.patient_id,
        start=body.start,
        duration_minutes=body.duration_minutes,
        fee_cents=fees.consultation_fee(doctor["fee_cents"], patient["insured"], body.duration_minutes),
        created_at=now,
    )
    store.appointments[appt.id] = appt
    return appt


@router.get("/appointments")
def list_appointments(
    status: Status | None = None,
    doctor_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    rows = sorted(store.appointments.values(), key=lambda a: (a.start, a.id))
    if status:
        rows = [a for a in rows if a.status == status]
    if doctor_id:
        rows = [a for a in rows if a.doctor_id == doctor_id]

    offset = (page - 1) * page_size
    items = rows[max(offset - 1, 0): offset + page_size]
    return {"items": items, "total": len(rows), "page": page, "page_size": page_size}


@router.get("/appointments/today")
def todays_appointments():
    """Appointments whose clinic-local date is today (clinic-local)."""
    today = clock.now_utc().date()
    return [
        a
        for a in sorted(store.appointments.values(), key=lambda a: a.start)
        if scheduling.to_local(a.start).date() == today
    ]


@router.get("/appointments/{appointment_id}")
def get_appointment(appointment_id: int) -> Appointment:
    return _get(appointment_id)


@router.post("/appointments/{appointment_id}/check-in")
def check_in(appointment_id: int) -> Appointment:
    appt = _get(appointment_id)
    _move(appt, "checked_in")
    return appt


@router.post("/appointments/{appointment_id}/complete")
def complete(appointment_id: int) -> Appointment:
    appt = _get(appointment_id)
    _move(appt, "completed")
    return appt


@router.post("/appointments/{appointment_id}/no-show")
def no_show(appointment_id: int) -> Appointment:
    appt = _get(appointment_id)
    if clock.now_utc() < appt.start:
        raise DomainError("Cannot mark no-show before the appointment starts", 409)
    _move(appt, "no_show")
    appt.cancellation_fee_cents = fees.no_show_fee(appt.fee_cents)
    return appt


@router.post("/appointments/{appointment_id}/cancel")
def cancel(appointment_id: int) -> Appointment:
    appt = _get(appointment_id)
    if appt.status == "cancelled":
        raise DomainError("Appointment is already cancelled", 409)

    hours_left = (appt.start - clock.now_utc()).total_seconds() / 3600
    if hours_left >= config.CANCEL_FREE_HOURS:
        appt.cancellation_fee_cents = 0
    else:
        appt.cancellation_fee_cents = fees.late_cancellation_fee(appt.fee_cents)
    appt.status = "cancelled"
    return appt


@router.delete("/appointments/{appointment_id}", status_code=204)
def delete_appointment(appointment_id: int, x_admin_token: str | None = Header(default=None)):
    require_admin(x_admin_token)
    _get(appointment_id)
    del store.appointments[appointment_id]
    return Response(status_code=204)
