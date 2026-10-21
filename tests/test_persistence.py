from app.store import Store
from tests.helpers import book


def test_appointment_survives_restart(client, tmp_path, monkeypatch):
    from app import routes

    db = Store(tmp_path / "t.db")
    monkeypatch.setattr(routes, "store", db)
    r = book(client, "2026-10-14T09:00:00-04:00")
    assert r.status_code == 201

    reopened = Store(tmp_path / "t.db")
    assert reopened.appointments == db.appointments
    assert reopened.next_id() == r.json()["id"] + 1
