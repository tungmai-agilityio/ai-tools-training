from app import config, demo
from app.main import app
from app.store import store
from fastapi.testclient import TestClient


def test_seeds_appointments_but_no_users_when_enabled_on_an_empty_db(anon_client, monkeypatch):
    monkeypatch.setattr(config, "DEMO_SEED", True)
    monkeypatch.setattr(config, "ADMIN_USERNAME", "")  # no admin seeding: the demo seed must not create accounts itself
    with TestClient(app):  # runs the lifespan
        assert len(store.appointments) == len(demo.TIMES) and not store.users


def test_adds_nothing_when_disabled(anon_client, monkeypatch):
    monkeypatch.setattr(config, "DEMO_SEED", False)
    with TestClient(app):
        assert not store.appointments


def test_restart_does_not_duplicate(anon_client, monkeypatch):
    monkeypatch.setattr(config, "DEMO_SEED", True)
    for _ in range(2):
        with TestClient(app):
            pass
    assert len(store.appointments) == len(demo.TIMES)
