import os

# Clinic-local timezone. All business hours below are expressed in this zone.
CLINIC_TIMEZONE = os.getenv("CLINIC_TIMEZONE", "America/New_York")

# SQLite file holding appointments (":memory:" in tests).
DB_PATH = os.getenv("DB_PATH", "data/clinic.db")

# Session signing key; empty means login is refused (fail closed).
AUTH_SECRET = os.getenv("AUTH_SECRET", "")
AUTH_SECRET_MIN_LENGTH = 32
# First admin, seeded at startup only when the users table is empty.
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
# Set COOKIE_SECURE=false only for plain-http local demos.
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").lower() != "false"
SESSION_COOKIE = "clinic_session"
SESSION_TTL_HOURS = 8
LOCKOUT_FAILURES = 5
LOCKOUT_MINUTES = 15
MIN_PASSWORD_LENGTH = 12

# Business hours, in minutes after local midnight.
WORK_START = 8 * 60
WORK_END = 17 * 60
LUNCH_START = 12 * 60
LUNCH_END = 13 * 60
SLOT_MINUTES = 30

MAX_DAYS_AHEAD = 60
CANCEL_FREE_HOURS = 24
