import importlib.util
from pathlib import Path

import pytest

from app import auth
from app.store import store
from tests.helpers import make_user

spec = importlib.util.spec_from_file_location("seed_admin", Path(__file__).resolve().parent.parent / "scripts" / "seed_admin.py")
seed_admin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seed_admin)

PW = "a long passphrase 12"


def test_creates_an_admin_that_can_log_in_without_a_forced_change(anon_client):
    assert seed_admin.create_or_reset_admin("boss", PW) == "created"
    (user,) = store.users.values()
    assert user.role == "admin" and not user.must_change_password and PW not in user.password_hash
    r = anon_client.post("/auth/login", json={"username": "boss", "password": PW})
    assert r.status_code == 200 and r.json()["must_change_password"] is False


def test_resets_an_existing_locked_staff_user_even_when_users_exist(anon_client):
    make_user(username="nurse1", failed_attempts=3, locked_until=None, active=False)
    make_user(username="other")
    version = store.get_user_by_name("nurse1").session_version
    assert seed_admin.create_or_reset_admin("Nurse1", PW) == "reset"
    user = store.get_user_by_name("nurse1")
    assert user.role == "admin" and user.active and user.failed_attempts == 0 and user.session_version == version + 1
    assert len(store.users) == 2
    assert anon_client.post("/auth/login", json={"username": "nurse1", "password": PW}).status_code == 200


def test_rejects_a_short_password_and_an_empty_name(anon_client):
    with pytest.raises(ValueError):
        seed_admin.create_or_reset_admin("boss", "x" * 11)
    with pytest.raises(ValueError):
        seed_admin.create_or_reset_admin("  ", PW)
    assert not store.users
