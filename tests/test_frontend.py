import shutil
import subprocess

import pytest


def test_index_page_is_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Clinic Booking" in r.text


def test_patients_endpoint_lists_seed_patients(client):
    body = client.get("/patients").json()
    assert [p["id"] for p in body] == [1, 2, 3]
    assert body[0]["insured"] is True


def test_index_page_offers_reschedule_for_scheduled_appointments(client):
    page = client.get("/").text
    assert 'btn("reschedule", "Reschedule")' in page
    assert "/reschedule`" in page


def test_reschedule_picker_offers_the_appointments_own_slots(client):
    # free_slots() counts the appointment being moved as busy; the page must add its own starts back.
    node = shutil.which("node")
    if not node:
        pytest.skip("node not installed")  # ponytail: JS check needs node; no JS test runner in this repo
    page = client.get("/").text
    start = page.index("function withOwnSlots")
    fn = page[start:page.index("\n}\n", start) + 2]
    script = 'const CLINIC_TZ = "America/New_York";\n' + fn + """
const appt = { start: "2026-10-14T14:00:00Z", duration_minutes: 60 };  // Wed 10:00-11:00 NY
const got = withOwnSlots(["2026-10-14T13:00:00+00:00", "2026-10-14T15:00:00+00:00"], appt, "2026-10-14");
const want = ["2026-10-14T13:00:00Z", "2026-10-14T14:00:00Z", "2026-10-14T14:30:00Z", "2026-10-14T15:00:00Z"];
if (JSON.stringify(got.map((s) => new Date(s).toISOString().replace(".000", ""))) !== JSON.stringify(want)) throw new Error(JSON.stringify(got));
if (withOwnSlots(["x"], appt, "2026-10-15").length !== 1) throw new Error("added slots on another day");
if (withOwnSlots(["x"], null, "2026-10-14").length !== 1) throw new Error("added slots outside reschedule mode");
"""
    r = subprocess.run([node, "-e", script], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
