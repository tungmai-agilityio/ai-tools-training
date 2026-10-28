from app import config
from app.store import store
from tests.helpers import make_user

PW = "correct horse battery"


def signed_in(anon_client, role="admin", username="boss"):
    make_user(username=username, role=role)
    assert anon_client.post("/auth/login", json={"username": username, "password": PW}).status_code == 200


def new_user(anon_client, username="nurse1", role="staff", password=PW):
    return anon_client.post("/users", json={"username": username, "password": password, "role": role})


def test_admin_creates_user_who_can_log_in(anon_client):  # TC-1
    signed_in(anon_client)
    r = new_user(anon_client)
    assert r.status_code == 201
    assert r.json()["username"] == "nurse1" and "password_hash" not in r.text and PW not in r.text
    assert any(u["username"] == "nurse1" for u in anon_client.get("/users").json())
    anon_client.post("/auth/logout")
    assert anon_client.post("/auth/login", json={"username": "nurse1", "password": PW}).status_code == 200


def test_duplicate_username_any_case_is_409(anon_client):  # TC-2
    signed_in(anon_client)
    new_user(anon_client)
    assert new_user(anon_client, username="Nurse1").status_code == 409


def test_short_password_is_422(anon_client):
    signed_in(anon_client)
    assert new_user(anon_client, password="x" * 11).status_code == 422


def test_disabling_ends_the_users_session(anon_client):  # TC-3
    from fastapi.testclient import TestClient
    from app.main import app

    signed_in(anon_client)
    uid = new_user(anon_client).json()["id"]
    staff = TestClient(app, base_url="https://testserver")
    assert staff.post("/auth/login", json={"username": "nurse1", "password": PW}).status_code == 200
    assert staff.get("/auth/me").status_code == 200
    assert anon_client.patch(f"/users/{uid}", json={"active": False}).status_code == 200
    assert staff.get("/auth/me").status_code == 401


def test_last_active_admin_cannot_be_disabled_or_demoted(anon_client):  # TC-4
    signed_in(anon_client)
    me = next(iter(store.users))
    assert anon_client.patch(f"/users/{me}", json={"active": False}).status_code == 409
    assert anon_client.patch(f"/users/{me}", json={"role": "staff"}).status_code == 409
    other = new_user(anon_client, username="boss2", role="admin").json()["id"]
    assert anon_client.patch(f"/users/{me}", json={"role": "staff"}).status_code == 200  # another admin exists
    assert other


def test_staff_gets_403_on_users_routes(anon_client):  # TC-5
    signed_in(anon_client, role="staff", username="nurse9")
    assert anon_client.get("/users").status_code == 403
    assert new_user(anon_client).status_code == 403
    assert anon_client.patch("/users/1", json={"active": False}).status_code == 403


def test_no_session_is_401_and_unknown_user_404(anon_client):
    assert anon_client.get("/users").status_code == 401
    signed_in(anon_client)
    assert anon_client.patch("/users/999", json={"active": True}).status_code == 404


def test_reenable_and_unlock_clear_the_lockout(anon_client):
    signed_in(anon_client)
    uid = new_user(anon_client).json()["id"]
    for _ in range(config.LOCKOUT_FAILURES):
        anon_client.post("/auth/login", json={"username": "nurse1", "password": "bad bad bad bad bad"})
    assert store.users[uid].locked_until is not None
    assert anon_client.patch(f"/users/{uid}", json={"active": True}).status_code == 200  # unlock
    assert store.users[uid].locked_until is None and store.users[uid].failed_attempts == 0
