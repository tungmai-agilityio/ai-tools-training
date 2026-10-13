from datetime import datetime, timezone


def now_utc() -> datetime:
    """Single source of 'now'. Tests replace this to freeze time."""
    return datetime.now(timezone.utc)
