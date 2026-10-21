"""Admin revenue report (T-015). Time is frozen at Tue 2026-10-13 10:00 New York."""

from datetime import datetime, timezone

import pytest

from app.models import Appointment
from app.store import store
from tests.helpers import book

ADMIN = {"x-admin-token": "s3cret"}
WED_9 = "2026-10-14T09:00:00-04:00"
WED_10 = "2026-10-14T10:00:00-04:00"
THU_9 = "2026-10-15T09:00:00-04:00"


@pytest.fixture(autouse=True)
def admin_token(monkeypatch):
    from app import config

    monkeypatch.setattr(config, "ADMIN_TOKEN", "s3cret")


def _report(client, frm, to, headers=ADMIN):
    return client.get("/reports/revenue", params={"from": frm, "to": to}, headers=headers)


def _complete(client, appt_id):
    assert client.post(f"/appointments/{appt_id}/check-in").status_code == 200
    assert client.post(f"/appointments/{appt_id}/complete").status_code == 200


def _doctor(body, doctor_id):
    return next(d for d in body["by_doctor"] if d["doctor_id"] == doctor_id)


def _direct(start_utc):
    """A completed 15000 visit saved straight to the store (no bookable slot differs by date between UTC and clinic time)."""
    appt = Appointment(
        id=store.next_id(), doctor_id=1, patient_id=1, start=start_utc, duration_minutes=30,
        status="completed", fee_cents=15000, created_at=datetime(2026, 10, 13, 14, 0, tzinfo=timezone.utc),
    )
    store.save(appt)


# --- consultation revenue -------------------------------------------------

def test_two_completed_visits_on_one_day_sum_into_consultation(client):
    _complete(client, book(client, WED_9, patient_id=1).json()["id"])  # insured: 12000
    _complete(client, book(client, WED_10, patient_id=2).json()["id"])  # 15000
    body = _report(client, "2026-10-14", "2026-10-14").json()
    assert body["totals"]["consultation_cents"] == 27000
    assert _doctor(body, 1)["consultation_cents"] == 27000


def test_doctor_and_day_breakdowns_add_up_to_the_grand_total(client):
    _complete(client, book(client, WED_9, doctor_id=1, patient_id=1).json()["id"])  # 12000
    _complete(client, book(client, THU_9, doctor_id=2, patient_id=2).json()["id"])  # 12997
    _complete(client, book(client, THU_9, doctor_id=1, patient_id=2).json()["id"])  # 15000
    body = _report(client, "2026-10-14", "2026-10-15").json()
    assert body["totals"] == {"consultation_cents": 39997, "penalty_cents": 0, "total_cents": 39997}
    assert [(d["doctor_id"], d["total_cents"]) for d in body["by_doctor"]] == [(1, 27000), (2, 12997), (3, 0)]
    assert [(d["date"], d["total_cents"]) for d in body["by_day"]] == [("2026-10-14", 12000), ("2026-10-15", 27997)]


def test_scheduled_checked_in_and_left_unseen_are_not_counted(client):
    book(client, WED_9, patient_id=1)
    checked_in = book(client, WED_10, patient_id=2).json()["id"]
    client.post(f"/appointments/{checked_in}/check-in")
    unseen = book(client, THU_9, patient_id=3).json()["id"]
    client.post(f"/appointments/{unseen}/check-in")
    client.post(f"/appointments/{unseen}/left-unseen")
    body = _report(client, "2026-10-14", "2026-10-15").json()
    assert body["totals"] == {"consultation_cents": 0, "penalty_cents": 0, "total_cents": 0}
    assert body["by_day"] == []


# --- penalty revenue ------------------------------------------------------

def test_late_cancel_and_no_show_count_as_penalty_not_consultation(client, now):
    late = book(client, WED_9, patient_id=1).json()["id"]  # fee 12000
    absent = book(client, THU_9, patient_id=2).json()["id"]  # fee 15000
    now["value"] = datetime(2026, 10, 14, 12, 0, tzinfo=timezone.utc)  # Wed 08:00 NY, 1h before
    assert client.post(f"/appointments/{late}/cancel").status_code == 200
    now["value"] = datetime(2026, 10, 15, 14, 0, tzinfo=timezone.utc)  # Thu 10:00 NY
    assert client.post(f"/appointments/{absent}/no-show").status_code == 200
    body = _report(client, "2026-10-14", "2026-10-15").json()
    assert body["totals"] == {"consultation_cents": 0, "penalty_cents": 21000, "total_cents": 21000}
    assert [(d["date"], d["penalty_cents"]) for d in body["by_day"]] == [("2026-10-14", 6000), ("2026-10-15", 15000)]


def test_free_cancellation_adds_nothing_and_no_day_row(client):
    appt_id = book(client, "2026-10-16T09:00:00-04:00").json()["id"]
    assert client.post(f"/appointments/{appt_id}/cancel").status_code == 200  # >24h ahead
    body = _report(client, "2026-10-16", "2026-10-16").json()
    assert body["totals"]["total_cents"] == 0
    assert body["by_day"] == []


# --- clinic-day boundary --------------------------------------------------

def test_late_evening_visit_counts_on_its_clinic_day(client):
    _direct(datetime(2026, 10, 15, 3, 0, tzinfo=timezone.utc))  # 2026-10-14 23:00 New York
    body = _report(client, "2026-10-14", "2026-10-14").json()
    assert body["totals"]["consultation_cents"] == 15000
    assert [d["date"] for d in body["by_day"]] == ["2026-10-14"]


def test_late_evening_visit_is_not_on_the_next_utc_day(client):
    _direct(datetime(2026, 10, 15, 3, 0, tzinfo=timezone.utc))
    body = _report(client, "2026-10-15", "2026-10-15").json()
    assert body["totals"]["total_cents"] == 0
    assert body["by_day"] == []


def test_visit_for_a_doctor_missing_from_the_seed_is_reported_as_unknown(client):
    _direct(datetime(2026, 10, 14, 13, 0, tzinfo=timezone.utc))
    store.appointments[1].doctor_id = 99
    r = _report(client, "2026-10-14", "2026-10-14")
    assert r.status_code == 200
    body = r.json()
    assert body["totals"]["consultation_cents"] == 15000
    assert _doctor(body, 99)["consultation_cents"] == 15000
    assert body["by_day"][0]["consultation_cents"] == 15000


# --- fee variants ---------------------------------------------------------

def test_insured_visit_counts_discounted_fee(client):
    _complete(client, book(client, WED_9, patient_id=1).json()["id"])
    assert _report(client, "2026-10-14", "2026-10-14").json()["totals"]["consultation_cents"] == 12000


def test_rescheduled_visit_counts_new_fee_on_new_day(client):
    appt_id = book(client, WED_9, patient_id=2).json()["id"]  # 15000
    r = client.post(f"/appointments/{appt_id}/reschedule", json={"start": THU_9, "duration_minutes": 60})
    assert r.status_code == 200
    _complete(client, appt_id)
    assert _report(client, "2026-10-14", "2026-10-14").json()["totals"]["total_cents"] == 0
    body = _report(client, "2026-10-15", "2026-10-15").json()
    assert body["totals"]["consultation_cents"] == 30000
    assert [d["date"] for d in body["by_day"]] == ["2026-10-15"]


def test_empty_range_lists_every_doctor_with_zero(client):
    r = _report(client, "2026-10-14", "2026-10-15")
    assert r.status_code == 200
    body = r.json()
    assert body["totals"] == {"consultation_cents": 0, "penalty_cents": 0, "total_cents": 0}
    assert [(d["doctor_id"], d["total_cents"]) for d in body["by_doctor"]] == [(1, 0), (2, 0), (3, 0)]
    assert body["by_day"] == []


# --- validation -----------------------------------------------------------

def test_from_after_to_is_rejected(client):
    assert _report(client, "2026-10-15", "2026-10-14").status_code == 422


def test_missing_from_or_to_is_rejected(client):
    assert client.get("/reports/revenue", params={"to": "2026-10-14"}, headers=ADMIN).status_code == 422
    assert client.get("/reports/revenue", params={"from": "2026-10-14"}, headers=ADMIN).status_code == 422


def test_malformed_date_is_rejected(client):
    assert _report(client, "yesterday", "2026-10-14").status_code == 422


def test_range_over_366_days_is_rejected(client):
    assert _report(client, "2026-01-01", "2027-01-02").status_code == 422  # 367 days inclusive


def test_range_of_exactly_366_days_is_allowed(client):
    assert _report(client, "2026-01-01", "2027-01-01").status_code == 200


# --- auth -----------------------------------------------------------------

def test_report_needs_admin_token(client):
    assert _report(client, "2026-10-14", "2026-10-14", headers={}).status_code == 403
    assert _report(client, "2026-10-14", "2026-10-14", headers={"x-admin-token": "wrong"}).status_code == 403


def test_report_refused_when_no_admin_token_configured(client, monkeypatch):
    from app import config

    monkeypatch.setattr(config, "ADMIN_TOKEN", "")
    assert _report(client, "2026-10-14", "2026-10-14", headers={"x-admin-token": ""}).status_code == 403
    assert _report(client, "2026-10-14", "2026-10-14").status_code == 403


def test_bad_token_gets_403_before_date_validation(client):
    assert client.get("/reports/revenue", params={"from": "nope"}, headers={"x-admin-token": "wrong"}).status_code == 403


# --- read-only ------------------------------------------------------------

def test_report_changes_no_stored_data(client):
    _complete(client, book(client, WED_9).json()["id"])
    before = {k: v.model_dump() for k, v in store.appointments.items()}
    assert _report(client, "2026-10-14", "2026-10-14").status_code == 200
    assert {k: v.model_dump() for k, v in store.appointments.items()} == before
