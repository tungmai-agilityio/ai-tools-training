import os
from datetime import datetime, timezone

os.environ.setdefault("CLINIC_TIMEZONE", "America/New_York")

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
def client(now):
    from app.main import app
    from app.store import store

    store.reset()
    return TestClient(app)
