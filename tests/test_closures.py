"""Clinic holidays and doctor time off (T-014). Time is frozen at Tue 2026-10-13 10:00 New York."""

from tests.helpers import book

WED_9AM = "2026-10-14T09:00:00-04:00"


def _holiday(client, day="2026-10-14", name="Founders Day"):
    return client.post("/holidays", json={"date": day, "name": name})


def _time_off(client, start="2026-10-14", end="2026-10-15", doctor_id=1):
    return client.post(f"/doctors/{doctor_id}/time-off", json={"start_date": start, "end_date": end, "reason": "Conference"})


def _slots(client, day, doctor_id=1):
    return client.get(f"/doctors/{doctor_id}/slots", params={"date": day}).json()


# --- clinic holidays ------------------------------------------------------

def test_holiday_needs_admin_role(client, staff_client):
    assert _holiday(staff_client).status_code == 403
    assert client.get("/holidays").json() == []


def test_holiday_has_no_slots_for_any_doctor_and_says_why(client):
    assert _holiday(client).status_code == 201
    for doctor_id in (1, 2, 3):
        body = _slots(client, "2026-10-14", doctor_id)
        assert body["slots"] == []
        assert body["closed"] == "Clinic is closed for Founders Day"
    assert _slots(client, "2026-10-15")["closed"] is None


def test_booking_on_a_holiday_is_422(client):
    _holiday(client)
    r = book(client, WED_9AM)
    assert r.status_code == 422
    assert "Founders Day" in r.json()["detail"]


def test_reschedule_onto_a_holiday_is_422(client):
    appt_id = book(client, "2026-10-15T09:00:00-04:00").json()["id"]
    _holiday(client)
    assert client.post(f"/appointments/{appt_id}/reschedule", json={"start": WED_9AM}).status_code == 422


def test_holiday_on_a_day_with_appointments_is_refused(client):
    appt_id = book(client, WED_9AM, doctor_id=2).json()["id"]
    r = _holiday(client)
    assert r.status_code == 409
    assert str(appt_id) in r.json()["detail"]


def test_cancelled_appointments_do_not_block_a_holiday(client):
    appt_id = book(client, WED_9AM).json()["id"]
    client.post(f"/appointments/{appt_id}/cancel")
    assert _holiday(client).status_code == 201


def test_holiday_uses_the_clinic_day_not_the_utc_day(client):
    # 16:30 New York is 20:30 UTC the same day; an appointment the evening before must stay bookable.
    _holiday(client, day="2026-10-15")
    assert book(client, "2026-10-15T16:30:00-04:00").status_code == 422
    assert book(client, "2026-10-14T16:30:00-04:00").status_code == 201


def test_duplicate_holiday_is_409(client):
    _holiday(client)
    assert _holiday(client).status_code == 409


def test_removing_a_holiday_reopens_the_day(client):
    _holiday(client)
    assert client.delete("/holidays/2026-10-14").status_code == 204
    assert _slots(client, "2026-10-14")["slots"]
    assert book(client, WED_9AM).status_code == 201
    assert client.delete("/holidays/2026-10-14").status_code == 404


# --- doctor time off ------------------------------------------------------

def test_time_off_needs_admin_role(staff_client):
    assert _time_off(staff_client).status_code == 403


def test_time_off_blocks_every_day_in_the_range_for_that_doctor_only(client):
    assert _time_off(client).status_code == 201
    for day in ("2026-10-14", "2026-10-15"):
        assert _slots(client, day) == {"doctor_id": 1, "date": day, "slots": [], "closed": "Doctor is on time off that day"}
        assert _slots(client, day, doctor_id=2)["slots"]
    assert _slots(client, "2026-10-16")["slots"]


def test_booking_a_doctor_on_time_off_is_409(client):
    _time_off(client)
    assert book(client, "2026-10-15T09:00:00-04:00").status_code == 409
    assert book(client, "2026-10-15T09:00:00-04:00", doctor_id=2).status_code == 201


def test_reschedule_into_time_off_is_409(client):
    appt_id = book(client, "2026-10-16T09:00:00-04:00").json()["id"]
    _time_off(client)
    assert client.post(f"/appointments/{appt_id}/reschedule", json={"start": WED_9AM}).status_code == 409


def test_time_off_over_existing_appointments_is_refused(client):
    book(client, "2026-10-15T09:00:00-04:00", doctor_id=2)  # another doctor: no clash
    appt_id = book(client, "2026-10-15T11:00:00-04:00").json()["id"]
    r = _time_off(client)
    assert r.status_code == 409
    assert str(appt_id) in r.json()["detail"]


def test_time_off_end_before_start_is_422(client):
    assert _time_off(client, start="2026-10-15", end="2026-10-14").status_code == 422


def test_time_off_for_unknown_doctor_is_404(client):
    assert _time_off(client, doctor_id=99).status_code == 404


def test_time_off_is_listed_and_can_be_removed(client):
    entry = _time_off(client).json()
    assert client.get("/doctors/1/time-off").json() == [entry]
    assert client.get("/doctors/2/time-off").json() == []
    assert client.delete(f"/doctors/2/time-off/{entry['id']}").status_code == 404
    assert client.delete(f"/doctors/1/time-off/{entry['id']}").status_code == 204
    assert book(client, WED_9AM).status_code == 201


# --- persistence ----------------------------------------------------------

def test_holidays_and_time_off_survive_a_restart(tmp_path):
    from datetime import date

    from app.models import Holiday, TimeOffIn
    from app.store import Store

    db = Store(tmp_path / "t.db")
    db.save_holiday(Holiday(date=date(2026, 12, 25), name="Christmas"))
    entry = db.add_time_off(2, TimeOffIn(start_date=date(2026, 11, 2), end_date=date(2026, 11, 6)))

    reopened = Store(tmp_path / "t.db")
    assert reopened.holidays[date(2026, 12, 25)].name == "Christmas"
    assert reopened.time_off[entry.id] == entry

    reopened.delete_time_off(entry.id)  # even the highest id is not handed out again after a restart
    later = Store(tmp_path / "t.db").add_time_off(2, TimeOffIn(start_date=date(2026, 11, 9), end_date=date(2026, 11, 9)))
    assert later.id > entry.id


def test_time_off_ids_are_never_reused_after_a_delete(client):
    first = _time_off(client, start="2026-10-14", end="2026-10-14").json()["id"]
    second = _time_off(client, start="2026-10-15", end="2026-10-15").json()["id"]
    client.delete(f"/doctors/1/time-off/{second}")
    third = _time_off(client, start="2026-10-16", end="2026-10-16").json()["id"]
    assert len({first, second, third}) == 3
    assert [t["id"] for t in client.get("/doctors/1/time-off").json()] == [first, third]
