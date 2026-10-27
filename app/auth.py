"""Password hashing, signed session cookie and the first-admin seed (stdlib only, see ADR-0002)."""

import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, Request, Response

from app import clock, config
from app.errors import DomainError
from app.models import UserRecord
from app.store import store

log = logging.getLogger(__name__)

_SCRYPT = {"n": 2**14, "r": 8, "p": 1}


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, **_SCRYPT)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    salt, digest = stored.split("$")
    check = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), **_SCRYPT)
    return hmac.compare_digest(check, bytes.fromhex(digest))


# Checked for unknown usernames so a miss costs the same as a wrong password.
DUMMY_HASH = hash_password("not-a-real-password")


def _sign(payload: str) -> str:
    return hmac.new(config.AUTH_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()


def issue_session(user: UserRecord) -> tuple[str, datetime]:
    """Return the signed cookie value and its expiry."""
    expires = clock.now_utc() + timedelta(hours=config.SESSION_TTL_HOURS)
    payload = f"{user.id}.{user.session_version}.{int(expires.timestamp())}"
    return f"{payload}.{_sign(payload)}", expires


def set_session_cookie(response: Response, value: str) -> None:
    response.set_cookie(
        config.SESSION_COOKIE, value, max_age=config.SESSION_TTL_HOURS * 3600,
        httponly=True, samesite="strict", secure=config.COOKIE_SECURE, path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(config.SESSION_COOKIE, httponly=True, samesite="strict", secure=config.COOKIE_SECURE, path="/")


def read_session(value: str | None) -> tuple[UserRecord, datetime]:
    """Verify a cookie value; raise 401 if it is missing, forged, expired or its user is gone/disabled."""
    unauth = DomainError("Not authenticated", 401)
    if not value or not config.AUTH_SECRET:
        raise unauth
    payload, _, sig = value.rpartition(".")
    if not hmac.compare_digest(sig, _sign(payload)):
        raise unauth
    try:
        user_id, version, exp = (int(x) for x in payload.split("."))
    except ValueError:
        raise unauth
    expires = datetime.fromtimestamp(exp, timezone.utc)
    user = store.users.get(user_id)
    if clock.now_utc() >= expires or user is None or not user.active or user.session_version != version:
        raise unauth
    return user, expires


def session_user(request: Request) -> tuple[UserRecord, datetime]:
    """Dependency: the signed-in user even if they still must change their password."""
    return read_session(request.cookies.get(config.SESSION_COOKIE))


def current_user(request: Request) -> UserRecord:
    """Dependency: the signed-in user; refused until a pending password change is done (DDR-0002)."""
    user, _ = session_user(request)
    if user.must_change_password:
        raise DomainError("Password change required", 403)
    return user


def require_role(role: str):
    """Dependency factory: any signed-in user for "staff"; admins only for "admin"."""

    def check(user: UserRecord = Depends(current_user)) -> UserRecord:
        if role == "admin" and user.role != "admin":
            raise DomainError("Administrator required", 403)
        return user

    return check


def set_password(user: UserRecord, password: str, must_change: bool) -> None:
    """Store a new password; ends every older session of the user and clears the lockout."""
    user.password_hash = hash_password(password)
    user.must_change_password = must_change
    user.session_version += 1
    user.failed_attempts, user.locked_until = 0, None


def seed_admin() -> None:
    """Create the first admin from ADMIN_USERNAME/ADMIN_PASSWORD, only when no user exists."""
    if store.users:
        return
    username, password = config.ADMIN_USERNAME.strip(), config.ADMIN_PASSWORD
    if not username or not password:
        log.warning("No users and ADMIN_USERNAME/ADMIN_PASSWORD are not both set: nobody can log in")
        return
    if len(password) < config.MIN_PASSWORD_LENGTH:
        raise RuntimeError(f"ADMIN_PASSWORD must be at least {config.MIN_PASSWORD_LENGTH} characters")
    store.save_user(UserRecord(
        id=store.next_user_id(), username=username, role="admin", must_change_password=True,
        created_at=clock.now_utc(), password_hash=hash_password(password),
    ))
