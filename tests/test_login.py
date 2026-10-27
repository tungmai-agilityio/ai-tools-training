from datetime import timedelta

import pytest

from app import auth, config
from app.main import app
from app.store import store
from fastapi.testclient import TestClient
from tests.helpers import make_user

PW = "correct horse battery"


def login(client, username="nurse1", password=PW):
    return client.post("/auth/login", json={"username": username, "password": password})


def test_login_ok_sets_secure_cookie_and_no_credential_in_body(client, now):  # TC-1
    make_user()
    r = login(client)
    assert r.status_code == 200
    body = r.json()
    assert body["username"] == "nurse1" and body["role"] == "staff" and body["must_change_password"] is False
    assert body["expires_at"].startswith("2026-10-13T22:00:00")  # frozen now 14:00Z + 8 h
    assert set(body) == {"username", "role", "expires_at", "must_change_password"}
    cookie = r.headers["set-cookie"].lower()
    for part in ("httponly", "samesite=strict", "secure", "path=/", "max-age=28800"):
        assert part in cookie
    assert client.get("/auth/me").json()["username"] == "nurse1"


def test_wrong_password_and_unknown_user_look_identical(client):  # TC-2
    make_user()
    a, b = login(client, password="nope nope nope nope"), login(client, username="ghost")
    assert a.status_code == b.status_code == 401
    assert a.json() == b.json()


def test_lockout_after_five_failures_and_recovery(client, now):  # TC-3
    make_user()
    for _ in range(5):
        assert login(client, password="bad bad bad bad bad").status_code == 401
    assert login(client).status_code == 423  # right password, still locked
    now["value"] += timedelta(minutes=15)
    assert login(client).status_code == 200


def test_success_resets_failure_count(client):  # TC-4
    make_user()
    for _ in range(4):
        login(client, password="bad bad bad bad bad")
    assert login(client).status_code == 200
    for _ in range(4):
        assert login(client, password="bad bad bad bad bad").status_code == 401
    assert login(client).status_code == 200


def test_me_rejects_expired_or_tampered_cookie(client, now):  # TC-5
    make_user()
    login(client)
    cookie = client.cookies.get(config.SESSION_COOKIE)
    now["value"] += timedelta(hours=8, seconds=1)
    assert client.get("/auth/me").status_code == 401
    now["value"] -= timedelta(hours=8, seconds=1)
    client.cookies.set(config.SESSION_COOKIE, cookie[:-1] + ("0" if cookie[-1] != "0" else "1"))
    assert client.get("/auth/me").status_code == 401


def test_logout_twice_clears_cookie(client):  # TC-7
    make_user()
    login(client)
    for _ in range(2):
        r = client.post("/auth/logout")
        assert r.status_code == 204
        assert "max-age=0" in r.headers["set-cookie"].lower()
    assert client.get("/auth/me").status_code == 401


def test_login_refused_without_secret(client, monkeypatch):
    make_user()
    monkeypatch.setattr(config, "AUTH_SECRET", "")
    assert login(client).status_code == 503


def test_disabled_user_cannot_log_in(client):
    make_user(active=False)
    assert login(client).status_code == 401


def test_pending_password_change_blocks_current_user_but_not_me(client):
    make_user(must_change_password=True)
    assert login(client).json()["must_change_password"] is True
    assert client.get("/auth/me").status_code == 200
    from fastapi import Request
    req = Request({"type": "http", "headers": [(b"cookie", f"{config.SESSION_COOKIE}={client.cookies.get(config.SESSION_COOKIE)}".encode())]})
    with pytest.raises(auth.DomainError) as e:
        auth.current_user(req)
    assert e.value.status == 403


# Seed (TC-6, TC-8, TC-9, TC-10): call seed_admin() on an empty store.
@pytest.fixture
def seed_env(client, monkeypatch):
    monkeypatch.setattr(config, "ADMIN_USERNAME", "firstadmin")
    monkeypatch.setattr(config, "ADMIN_PASSWORD", "seed password 123")


def test_seed_creates_hashed_admin_who_must_change_password(seed_env, client):  # TC-6
    auth.seed_admin()
    (user,) = store.users.values()
    assert user.role == "admin" and user.must_change_password and "seed password" not in user.password_hash
    assert login(client, "firstadmin", "seed password 123").json()["must_change_password"] is True


def test_seed_skipped_with_warning_when_setting_missing(seed_env, client, monkeypatch, caplog):  # TC-8
    monkeypatch.setattr(config, "ADMIN_PASSWORD", "")
    auth.seed_admin()
    assert not store.users and "ADMIN_USERNAME/ADMIN_PASSWORD" in caplog.text
    assert login(client, "firstadmin", "").status_code in (401, 422)


def test_seed_short_password_stops_startup(seed_env, client, monkeypatch):  # TC-9
    monkeypatch.setattr(config, "ADMIN_PASSWORD", "x" * 11)
    with pytest.raises(RuntimeError), TestClient(app):
        pass
    assert not store.users


def test_seed_ignored_when_users_exist(seed_env, client, monkeypatch):  # TC-10
    auth.seed_admin()
    monkeypatch.setattr(config, "ADMIN_PASSWORD", "a different password 9")
    auth.seed_admin()
    assert len(store.users) == 1
    assert login(client, "firstadmin", "seed password 123").status_code == 200


def test_weak_secret_refuses_login_and_stops_startup(client, monkeypatch):
    make_user()
    monkeypatch.setattr(config, "AUTH_SECRET", "x" * 31)
    assert login(client).status_code == 503
    with pytest.raises(RuntimeError), TestClient(app):
        pass
    monkeypatch.setattr(config, "AUTH_SECRET", "x" * 32)
    assert login(client).status_code == 200
