from app import config
from app.store import store
from tests.helpers import make_user

PW = "correct horse battery"


def signed_in(client, role="admin", username="boss"):
    make_user(username=username, role=role)
    assert client.post("/auth/login", json={"username": username, "password": PW}).status_code == 200


def new_user(client, username="nurse1", role="staff", password=PW):
    return client.post("/users", json={"username": username, "password": password, "role": role})


def test_admin_creates_user_who_can_log_in(client):  # TC-1
    signed_in(client)
    r = new_user(client)
    assert r.status_code == 201
    assert r.json()["username"] == "nurse1" and "password_hash" not in r.text and PW not in r.text
    assert any(u["username"] == "nurse1" for u in client.get("/users").json())
    client.post("/auth/logout")
    assert client.post("/auth/login", json={"username": "nurse1", "password": PW}).status_code == 200


def test_duplicate_username_any_case_is_409(client):  # TC-2
    signed_in(client)
    new_user(client)
    assert new_user(client, username="Nurse1").status_code == 409


def test_short_password_is_422(client):
    signed_in(client)
    assert new_user(client, password="x" * 11).status_code == 422


def test_disabling_ends_the_users_session(client):  # TC-3
    from fastapi.testclient import TestClient
    from app.main import app

    signed_in(client)
    uid = new_user(client).json()["id"]
    staff = TestClient(app, base_url="https://testserver")
    assert staff.post("/auth/login", json={"username": "nurse1", "password": PW}).status_code == 200
    assert staff.get("/auth/me").status_code == 200
    assert client.patch(f"/users/{uid}", json={"active": False}).status_code == 200
    assert staff.get("/auth/me").status_code == 401


def test_last_active_admin_cannot_be_disabled_or_demoted(client):  # TC-4
    signed_in(client)
    me = next(iter(store.users))
    assert client.patch(f"/users/{me}", json={"active": False}).status_code == 409
    assert client.patch(f"/users/{me}", json={"role": "staff"}).status_code == 409
    other = new_user(client, username="boss2", role="admin").json()["id"]
    assert client.patch(f"/users/{me}", json={"role": "staff"}).status_code == 200  # another admin exists
    assert other


def test_staff_gets_403_on_users_routes(client):  # TC-5
    signed_in(client, role="staff", username="nurse9")
    assert client.get("/users").status_code == 403
    assert new_user(client).status_code == 403
    assert client.patch("/users/1", json={"active": False}).status_code == 403


def test_no_session_is_401_and_unknown_user_404(client):
    assert client.get("/users").status_code == 401
    signed_in(client)
    assert client.patch("/users/999", json={"active": True}).status_code == 404


def test_reenable_and_unlock_clear_the_lockout(client, now):
    signed_in(client)
    uid = new_user(client).json()["id"]
    for _ in range(config.LOCKOUT_FAILURES):
        client.post("/auth/login", json={"username": "nurse1", "password": "bad bad bad bad bad"})
    assert store.users[uid].locked_until is not None
    assert client.patch(f"/users/{uid}", json={"active": True}).status_code == 200  # unlock
    assert store.users[uid].locked_until is None and store.users[uid].failed_attempts == 0
