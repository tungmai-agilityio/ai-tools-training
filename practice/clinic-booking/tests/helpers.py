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
