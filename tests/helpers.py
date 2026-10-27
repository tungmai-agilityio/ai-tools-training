def book(client, start, doctor_id=1, patient_id=1, duration=30):
    """POST an appointment. `start` is an ISO string with offset, e.g. 2026-10-14T09:00:00-04:00."""
    return client.post(
        "/appointments",
        json={
            "doctor_id": doctor_id,
            "patient_id": patient_id,
            "start": start,
            "duration_minutes": duration,
        },
    )


def make_user(username="nurse1", password="correct horse battery", role="staff", **extra):
    """Store a user directly (fake data) and return the record."""
    from app import auth, clock
    from app.models import UserRecord
    from app.store import store

    user = UserRecord(
        id=store.next_user_id(), username=username, role=role, created_at=clock.now_utc(),
        password_hash=auth.hash_password(password), **extra,
    )
    store.save_user(user)
    return user
