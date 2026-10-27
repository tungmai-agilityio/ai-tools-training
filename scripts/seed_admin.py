"""Create an admin, or reset one's password, straight in the database (no running server, no password in .env).

Usage:  python scripts/seed_admin.py USERNAME        (prompts twice for the password)

Reads DB_PATH from the environment like the app (source .env first). Works when users already exist:
an existing username gets the new password, the admin role, active status and no lockout, and its older
sessions end. Restart the server afterwards: it keeps users in memory and will not see this change.
The password you type is yours, so the account is not forced to change it.
"""
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import auth, clock, config  # noqa: E402
from app.models import UserRecord  # noqa: E402
from app.store import store  # noqa: E402


def create_or_reset_admin(username: str, password: str) -> str:
    """Return "created" or "reset". Raises ValueError for an empty name or a short password."""
    username = username.strip()
    if not username:
        raise ValueError("Username is required.")
    if len(password) < config.MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {config.MIN_PASSWORD_LENGTH} characters.")
    user = store.get_user_by_name(username)
    if user is None:
        store.save_user(UserRecord(
            id=store.next_user_id(), username=username, role="admin", created_at=clock.now_utc(),
            password_hash=auth.hash_password(password),
        ))
        return "created"
    auth.set_password(user, password, must_change=False)  # also bumps session_version and clears the lock
    user.role, user.active = "admin", True
    store.save_user(user)
    return "reset"


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    username = sys.argv[1]
    password = getpass.getpass("Password: ")
    if password != getpass.getpass("Repeat password: "):
        sys.exit("The passwords do not match.")
    try:
        result = create_or_reset_admin(username, password)
    except ValueError as e:
        sys.exit(str(e))
    print(f"Admin '{username.strip()}' {result} in {config.DB_PATH}. Restart the server so it picks this up.")


if __name__ == "__main__":
    main()
