import os
from datetime import datetime, timezone

os.environ.setdefault("CLINIC_TIMEZONE", "America/New_York")
os.environ.setdefault("DB_PATH", ":memory:")
os.environ.setdefault("AUTH_SECRET", "test-secret-not-real-0123456789abcdef")

import pytest
from fastapi.testclient import TestClient

# Tuesday 2026-10-13 10:00 clinic time (US Eastern, UTC-4 in October)
FIXED_NOW = datetime(2026, 10, 13, 14, 0, tzinfo=timezone.utc)


@pytest.fixture
def now(monkeypatch):
    """Mutable frozen clock: set now["value"] to move time."""
    from app import clock

    state = {"value": FIXED_NOW}
    monkeypatch.setattr(clock, "now_utc", lambda: state["value"])
    return state


@pytest.fixture
def anon_client(now):
    """A client with no session (empty store)."""
    from app.main import app
    from app.store import store

    store.reset()
    # https base URL so the Secure session cookie is sent back
    return TestClient(app, base_url="https://testserver")


@pytest.fixture
def client(anon_client):
    """A separate client signed in as an admin (shares the store with `anon_client`)."""
    from tests.helpers import login_as, make_user

    from app import config
    from app.main import app

    make_user(username="testadmin", role="admin")
    admin = TestClient(app, base_url="https://testserver")
    # Many tests move the frozen clock by days; keep this session alive across them.
    ttl, config.SESSION_TTL_HOURS = config.SESSION_TTL_HOURS, 24 * 3650
    try:
        login_as(admin, "testadmin")
    finally:
        config.SESSION_TTL_HOURS = ttl
    return admin


@pytest.fixture
def staff_client(anon_client):
    """A separate client signed in as staff (shares the store with `client`)."""
    from app import config
    from app.main import app
    from tests.helpers import login_as, make_user

    make_user(username="teststaff", role="staff")
    c = TestClient(app, base_url="https://testserver")
    ttl, config.SESSION_TTL_HOURS = config.SESSION_TTL_HOURS, 24 * 3650
    try:
        login_as(c, "teststaff")
    finally:
        config.SESSION_TTL_HOURS = ttl
    return c
