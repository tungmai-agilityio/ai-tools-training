from datetime import datetime, timezone

from tests.helpers import book

WED_9 = "2026-10-14T09:00:00-04:00"


# --- creating -----------------------------------------------------------

def test_book_returns_201_with_fee(client):
    r = book(client, WED_9, doctor_id=1, patient_id=2)
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "scheduled"
    assert body["fee_cents"] == 15000


def test_insured_patient_gets_discount(client):
    assert book(client, WED_9, patient_id=1).json()["fee_cents"] == 12000


def test_sixty_minute_booking_doubles_fee(client):
    assert book(client, WED_9, patient_id=2, duration=60).json()["fee_cents"] == 30000


def test_unknown_doctor_and_patient_are_404(client):
    assert book(client, WED_9, doctor_id=99).status_code == 404
    assert book(client, WED_9, patient_id=99).status_code == 404


def test_same_doctor_same_time_is_409(client):
    assert book(client, WED_9, patient_id=1).status_code == 201
    assert book(client, WED_9, patient_id=2).status_code == 409


def test_same_patient_two_doctors_same_time_is_409(client):
    assert book(client, WED_9, doctor_id=1, patient_id=1).status_code == 201
    assert book(client, WED_9, doctor_id=2, patient_id=1).status_code == 409


def test_back_to_back_is_allowed(client):
    assert book(client, WED_9).status_code == 201
    assert book(client, "2026-10-14T09:30:00-04:00").status_code == 201


def test_booking_inside_existing_long_visit_is_409(client):
    assert book(client, WED_9, patient_id=1, duration=60).status_code == 201
    assert book(client, "2026-10-14T09:30:00-04:00", patient_id=2).status_code == 409


def test_long_visit_over_existing_short_one_is_409(client):
    assert book(client, "2026-10-14T09:30:00-04:00", patient_id=1).status_code == 201
    assert book(client, WED_9, patient_id=2, duration=60).status_code == 409


def test_patient_cannot_overlap_long_visit_with_other_doctor(client):
    assert book(client, WED_9, doctor_id=1, patient_id=1, duration=60).status_code == 201
    assert book(client, "2026-10-14T09:30:00-04:00", doctor_id=2, patient_id=1).status_code == 409


def test_back_to_back_after_long_visit_is_allowed(client):
    assert book(client, WED_9, duration=60).status_code == 201
    assert book(client, "2026-10-14T10:00:00-04:00").status_code == 201


# --- lifecycle ----------------------------------------------------------

def test_check_in_then_complete(client):
    appt_id = book(client, WED_9).json()["id"]
    assert client.post(f"/appointments/{appt_id}/check-in").json()["status"] == "checked_in"
    assert client.post(f"/appointments/{appt_id}/complete").json()["status"] == "completed"


def test_cannot_complete_without_check_in(client):
    appt_id = book(client, WED_9).json()["id"]
    assert client.post(f"/appointments/{appt_id}/complete").status_code == 409


def test_no_show_after_start_charges_full_fee(client, now):
    appt_id = book(client, WED_9, patient_id=2).json()["id"]
    now["value"] = datetime(2026, 10, 14, 14, 0, tzinfo=timezone.utc)  # 10:00 local, after start
    r = client.post(f"/appointments/{appt_id}/no-show")
    assert r.status_code == 200
    assert r.json()["status"] == "no_show"
    assert r.json()["cancellation_fee_cents"] == 15000


def test_no_show_before_start_is_409(client):
    appt_id = book(client, WED_9).json()["id"]
    assert client.post(f"/appointments/{appt_id}/no-show").status_code == 409


# --- cancelling ---------------------------------------------------------

def test_cancel_more_than_24h_ahead_is_free(client):
    appt_id = book(client, "2026-10-15T09:00:00-04:00", patient_id=2).json()["id"]
    r = client.post(f"/appointments/{appt_id}/cancel")
    assert r.json()["status"] == "cancelled"
    assert r.json()["cancellation_fee_cents"] == 0


def test_late_cancel_charges_half(client):
    # now is Tue 10:00 local; 15:00 the same day is 5h away
    appt_id = book(client, "2026-10-13T15:00:00-04:00", patient_id=2).json()["id"]
    r = client.post(f"/appointments/{appt_id}/cancel")
    assert r.json()["cancellation_fee_cents"] == 7500


def test_cancel_twice_is_409(client):
    appt_id = book(client, WED_9).json()["id"]
    assert client.post(f"/appointments/{appt_id}/cancel").status_code == 200
    assert client.post(f"/appointments/{appt_id}/cancel").status_code == 409


def test_cancelled_slot_can_be_rebooked(client):
    appt_id = book(client, WED_9, patient_id=1).json()["id"]
    client.post(f"/appointments/{appt_id}/cancel")
    assert book(client, WED_9, patient_id=2).status_code == 201


def test_unknown_appointment_is_404(client):
    assert client.get("/appointments/999").status_code == 404
    assert client.post("/appointments/999/cancel").status_code == 404


# --- listing ------------------------------------------------------------

def _book_twelve(client):
    starts = ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
              "13:00", "13:30", "14:00", "14:30", "15:00", "15:30"]
    for s in starts:
        assert book(client, f"2026-10-14T{s}:00-04:00").status_code == 201


def _walk(client, page_size, **filters):
    """Fetch every page; return (ids in order, total reported)."""
    ids, page, total = [], 1, None
    while True:
        body = client.get(
            "/appointments", params={"page": page, "page_size": page_size, **filters}
        ).json()
        total = body["total"]
        if not body["items"]:
            break
        ids.extend(a["id"] for a in body["items"])
        page += 1
    return ids, total


def test_list_first_page(client):
    _book_twelve(client)
    body = client.get("/appointments", params={"page_size": 5}).json()
    assert body["total"] == 12
    assert [a["id"] for a in body["items"]] == [1, 2, 3, 4, 5]


def test_list_filters_by_status(client):
    a = book(client, WED_9).json()["id"]
    book(client, "2026-10-14T09:30:00-04:00")
    client.post(f"/appointments/{a}/cancel")
    body = client.get("/appointments", params={"status": "cancelled"}).json()
    assert [x["id"] for x in body["items"]] == [a]


def test_today_lists_todays_appointments(client):
    book(client, "2026-10-13T14:00:00-04:00", patient_id=2)
    book(client, WED_9, patient_id=3)
    today = client.get("/appointments/today").json()
    assert len(today) == 1


def test_today_uses_clinic_date_late_in_the_evening(client, now):
    book(client, "2026-10-13T15:00:00-04:00", patient_id=2)
    book(client, WED_9, patient_id=3)
    now["value"] = datetime(2026, 10, 14, 1, 0, tzinfo=timezone.utc)  # Tue 9 PM in New York
    today = client.get("/appointments/today").json()
    assert [a["patient_id"] for a in today] == [2]


def test_pages_are_disjoint_and_cover_everything(client):
    _book_twelve(client)
    ids, total = _walk(client, page_size=5)  # 5 + 5 + 2
    assert total == 12
    assert len(ids) == len(set(ids)) == 12
    assert sorted(ids) == list(range(1, 13))


def test_last_partial_page_has_no_overlap_with_previous(client):
    _book_twelve(client)
    p2 = client.get("/appointments", params={"page": 2, "page_size": 5}).json()["items"]
    p3 = client.get("/appointments", params={"page": 3, "page_size": 5}).json()["items"]
    assert len(p3) == 2
    assert {a["id"] for a in p2}.isdisjoint({a["id"] for a in p3})


def test_page_size_that_divides_total_has_no_repeated_page(client):
    _book_twelve(client)
    ids, _ = _walk(client, page_size=4)
    assert len(ids) == len(set(ids)) == 12


def test_page_size_one_returns_each_appointment_once(client):
    _book_twelve(client)
    ids, _ = _walk(client, page_size=1)
    assert len(ids) == len(set(ids)) == 12


def test_page_beyond_last_is_empty_but_total_is_unchanged(client):
    _book_twelve(client)
    body = client.get("/appointments", params={"page": 99, "page_size": 5}).json()
    assert body["items"] == []
    assert body["total"] == 12


def test_same_page_requested_twice_is_identical(client):
    _book_twelve(client)
    a = client.get("/appointments", params={"page": 2, "page_size": 5}).json()
    b = client.get("/appointments", params={"page": 2, "page_size": 5}).json()
    assert a == b


# --- admin delete -------------------------------------------------------

def test_admin_delete_requires_token(client, monkeypatch):
    from app import config

    monkeypatch.setattr(config, "ADMIN_TOKEN", "s3cret")
    appt_id = book(client, WED_9).json()["id"]
    assert client.delete(f"/appointments/{appt_id}").status_code == 403
    assert client.delete(f"/appointments/{appt_id}", headers={"x-admin-token": "s3cret"}).status_code == 204
    assert client.get(f"/appointments/{appt_id}").status_code == 404
