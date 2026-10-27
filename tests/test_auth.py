from datetime import timedelta

import pytest

from app import auth, config
from app.errors import DomainError
from tests.helpers import make_user


def test_password_hash_verifies_and_is_salted():
    h1, h2 = auth.hash_password("correct horse battery"), auth.hash_password("correct horse battery")
    assert h1 != h2 and "correct" not in h1
    assert auth.verify_password("correct horse battery", h1)
    assert not auth.verify_password("wrong", h1)


def test_session_round_trip(anon_client, now):
    user = make_user()
    value, expires = auth.issue_session(user)
    got, got_exp = auth.read_session(value)
    assert got.id == user.id and got_exp == expires
    assert expires == now["value"] + timedelta(hours=8)


def test_session_rejected_when_expired_or_tampered(anon_client, now):
    value, _ = auth.issue_session(make_user())
    now["value"] += timedelta(hours=8, seconds=1)
    with pytest.raises(DomainError) as e:
        auth.read_session(value)
    assert e.value.status == 401
    now["value"] -= timedelta(hours=8)
    for bad in (value[:-1] + ("0" if value[-1] != "0" else "1"), "garbage", "", None):
        with pytest.raises(DomainError):
            auth.read_session(bad)


def test_session_rejected_without_secret_or_after_version_bump(anon_client, monkeypatch):
    user = make_user()
    value, _ = auth.issue_session(user)
    user.session_version += 1
    with pytest.raises(DomainError):
        auth.read_session(value)
    user.session_version -= 1
    monkeypatch.setattr(config, "AUTH_SECRET", "")
    with pytest.raises(DomainError):
        auth.read_session(value)
