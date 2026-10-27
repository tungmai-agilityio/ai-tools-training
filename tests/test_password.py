from fastapi.testclient import TestClient

from app.main import app
from tests.helpers import login_as, make_user

PW = "correct horse battery"
NEW = "another long passphrase"


def change(c, current=PW, new=NEW):
    return c.post("/auth/change-password", json={"current_password": current, "new_password": new})


def other_client():
    return TestClient(app, base_url="https://testserver")


def test_change_password_switches_the_login(anon_client):  # TC-1
    make_user()
    login_as(anon_client, "nurse1")
    r = change(anon_client)
    assert r.status_code == 204
    assert anon_client.get("/auth/me").status_code == 200  # fresh cookie keeps this session
    assert other_client().post("/auth/login", json={"username": "nurse1", "password": PW}).status_code == 401
    assert other_client().post("/auth/login", json={"username": "nurse1", "password": NEW}).status_code == 200


def test_wrong_current_password_is_403_and_changes_nothing(anon_client):  # TC-2
    make_user()
    login_as(anon_client, "nurse1")
    assert change(anon_client, current="not the password").status_code == 403
    assert other_client().post("/auth/login", json={"username": "nurse1", "password": PW}).status_code == 200


def test_short_or_unchanged_new_password_is_422(anon_client):  # TC-3
    make_user()
    login_as(anon_client, "nurse1")
    assert change(anon_client, new="x" * 11).status_code == 422
    assert change(anon_client, new=PW).status_code == 422


def test_change_requires_a_session(anon_client):
    assert change(anon_client).status_code == 401


def test_admin_reset_returns_a_temporary_password_once(client, staff_client):  # TC-4
    nurse = make_user(username="nurse1")
    r = client.post(f"/users/{nurse.id}/reset-password")
    assert r.status_code == 200 and r.headers["cache-control"] == "no-store"
    temp = r.json()["temporary_password"]
    assert len(temp) >= 12 and temp != PW
    assert temp not in client.get("/users").text  # never shown again
    assert staff_client.post(f"/users/{nurse.id}/reset-password").status_code == 403
    assert client.post("/users/999/reset-password").status_code == 404


def test_temporary_password_login_is_gated_until_changed(client, anon_client):  # TC-5
    nurse = make_user(username="nurse1")
    temp = client.post(f"/users/{nurse.id}/reset-password").json()["temporary_password"]
    r = anon_client.post("/auth/login", json={"username": "nurse1", "password": temp})
    assert r.status_code == 200 and r.json()["must_change_password"] is True
    assert anon_client.post("/appointments", json={}).status_code == 403
    assert anon_client.get("/doctors").status_code == 403
    assert anon_client.get("/auth/me").status_code == 200
    assert change(anon_client, current=temp).status_code == 204
    assert anon_client.get("/doctors").status_code == 200  # gate lifted, fresh cookie


def test_change_and_reset_end_older_sessions_and_clear_the_lockout(client, anon_client):  # TC-6
    nurse = make_user(username="nurse1")
    old = other_client()
    login_as(old, "nurse1")
    assert old.get("/auth/me").status_code == 200
    for _ in range(5):
        anon_client.post("/auth/login", json={"username": "nurse1", "password": "bad bad bad bad bad"})
    assert anon_client.post("/auth/login", json={"username": "nurse1", "password": PW}).status_code == 423
    temp = client.post(f"/users/{nurse.id}/reset-password").json()["temporary_password"]
    assert old.get("/auth/me").status_code == 401  # TC-6: old cookie no longer works
    assert anon_client.post("/auth/login", json={"username": "nurse1", "password": temp}).status_code == 200  # lock cleared
