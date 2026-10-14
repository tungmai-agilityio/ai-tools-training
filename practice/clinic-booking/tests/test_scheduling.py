from datetime import datetime, timedelta, timezone

import pytest

from tests.helpers import book

WED = "2026-10-14"  # a weekday after the frozen "now"
SAT = "2026-10-17"


def local_hours(slots):
    tz = timezone(timedelta(hours=-4))
    return [datetime.fromisoformat(s).astimezone(tz).strftime("%H:%M") for s in slots]


def test_weekday_has_16_slots_and_skips_lunch(client):
    slots = client.get("/doctors/1/slots", params={"date": WED}).json()["slots"]
    hours = local_hours(slots)
    assert len(slots) == 16
    assert hours[0] == "08:00"
    assert hours[-1] == "16:30"
    assert "12:00" not in hours and "12:30" not in hours


def test_weekend_has_no_slots(client):
    assert client.get("/doctors/1/slots", params={"date": SAT}).json()["slots"] == []


def test_booked_slot_disappears(client):
    assert book(client, f"{WED}T09:00:00-04:00").status_code == 201
    hours = local_hours(client.get("/doctors/1/slots", params={"date": WED}).json()["slots"])
    assert "09:00" not in hours
    assert "09:30" in hours


def test_long_visit_hides_both_slots(client):
    assert book(client, f"{WED}T09:00:00-04:00", duration=60).status_code == 201
    hours = local_hours(client.get("/doctors/1/slots", params={"date": WED}).json()["slots"])
    assert "09:00" not in hours
    assert "09:30" not in hours
    assert "10:00" in hours


@pytest.mark.parametrize(
    "start,duration",
    [
        ("2026-10-12T09:00:00-04:00", 30),  # in the past
        ("2026-10-17T09:00:00-04:00", 30),  # Saturday
        ("2026-10-14T12:00:00-04:00", 30),  # lunch
        ("2026-10-14T11:30:00-04:00", 60),  # runs into lunch
        ("2026-10-14T09:15:00-04:00", 30),  # off the 30-minute grid
        ("2026-10-14T07:30:00-04:00", 30),  # before opening
        ("2026-10-14T17:00:00-04:00", 30),  # after closing
        ("2026-10-14T16:30:00-04:00", 60),  # runs past closing
        ("2027-01-14T09:00:00-05:00", 30),  # more than 60 days ahead
    ],
)
def test_invalid_start_is_rejected(client, start, duration):
    assert book(client, start, duration=duration).status_code == 422


def test_start_without_timezone_is_rejected(client):
    assert book(client, "2026-10-14T09:00:00").status_code == 422


def test_unknown_doctor_slots_404(client):
    assert client.get("/doctors/99/slots", params={"date": WED}).status_code == 404
