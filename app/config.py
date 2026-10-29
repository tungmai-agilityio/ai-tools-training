"""Settings read from the environment (and the repo-root .env), plus fixed business-hour constants."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    """Environment variables win over .env; unknown variables are ignored."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore", hide_input_in_errors=True)

    # Clinic-local timezone. All business hours below are expressed in this zone.
    clinic_timezone: str = "America/New_York"
    # SQLite file holding appointments (":memory:" in tests).
    db_path: str = "data/clinic.db"
    # Session signing key; empty means login is refused (fail closed).
    auth_secret: str = ""
    # First admin, seeded at startup only when the users table is empty.
    admin_username: str = ""
    admin_password: str = ""
    # Set COOKIE_SECURE=false only for plain-http local demos.
    cookie_secure: bool = True
    # DEMO_SEED=1 books demo appointments at startup while none exist (hosted test site).
    demo_seed: bool = False
    # Set by Render to the commit it is running; /health reports it so a deploy can be verified.
    render_git_commit: str | None = None


settings = Settings()

# The app reads these names, and tests patch them on this module.
CLINIC_TIMEZONE = settings.clinic_timezone
DB_PATH = settings.db_path
AUTH_SECRET = settings.auth_secret
ADMIN_USERNAME = settings.admin_username
ADMIN_PASSWORD = settings.admin_password
COOKIE_SECURE = settings.cookie_secure
DEMO_SEED = settings.demo_seed
RENDER_GIT_COMMIT = (settings.render_git_commit or "").strip() or None

AUTH_SECRET_MIN_LENGTH = 32
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
