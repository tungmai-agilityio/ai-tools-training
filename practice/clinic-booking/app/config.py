import os

# Clinic-local timezone. All business hours below are expressed in this zone.
CLINIC_TIMEZONE = os.getenv("CLINIC_TIMEZONE", "America/New_York")

# Token for admin-only endpoints (see routes.require_admin).
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

# Business hours, in minutes after local midnight.
WORK_START = 8 * 60
WORK_END = 17 * 60
LUNCH_START = 12 * 60
LUNCH_END = 13 * 60
SLOT_MINUTES = 30

MAX_DAYS_AHEAD = 60
CANCEL_FREE_HOURS = 24
