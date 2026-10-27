import threading
from datetime import timedelta

from fastapi import APIRouter, Depends, Request, Response

from app import auth, clock, config
from app.errors import DomainError
from app.models import ChangePasswordIn, LoginIn, SessionOut, UserRecord
from app.store import store

router = APIRouter(prefix="/auth", tags=["auth"])

# ponytail: one lock per existing user id (the dict only grows with real users) makes check, verify and
# counter update atomic so parallel guesses cannot skip the lockout; unknown names never take a lock.
# Add per-IP rate limiting if the app is exposed beyond the clinic network.
_user_locks: dict[int, threading.Lock] = {}


def _session_out(user: UserRecord, expires) -> SessionOut:
    return SessionOut(username=user.username, role=user.role, expires_at=expires, must_change_password=user.must_change_password)


@router.post("/login")
def login(body: LoginIn, response: Response) -> SessionOut:
    if not config.AUTH_SECRET:
        raise DomainError("Login is not configured", 503)
    user = store.get_user_by_name(body.username)
    if user is None:
        auth.verify_password(body.password, auth.DUMMY_HASH)
        raise DomainError("Wrong username or password", 401)
    with _user_locks.setdefault(user.id, threading.Lock()):
        return _login(user, body, response)


def _login(user: UserRecord, body: LoginIn, response: Response) -> SessionOut:
    now = clock.now_utc()
    if user.locked_until and now < user.locked_until:
        raise DomainError("Too many failed attempts. Try again later.", 423)
    if not user.active:
        auth.verify_password(body.password, auth.DUMMY_HASH)
        raise DomainError("Wrong username or password", 401)
    if not auth.verify_password(body.password, user.password_hash):
        user.failed_attempts += 1
        if user.failed_attempts >= config.LOCKOUT_FAILURES:
            user.failed_attempts = 0
            user.locked_until = now + timedelta(minutes=config.LOCKOUT_MINUTES)
        store.save_user(user)
        raise DomainError("Wrong username or password", 401)
    user.failed_attempts, user.locked_until = 0, None
    store.save_user(user)
    value, expires = auth.issue_session(user)
    auth.set_session_cookie(response, value)
    return _session_out(user, expires)


@router.post("/logout", status_code=204)
def logout() -> Response:
    response = Response(status_code=204)
    auth.clear_session_cookie(response)
    return response


@router.get("/me")
def me(session=Depends(auth.session_user)) -> SessionOut:
    return _session_out(*session)


@router.post("/change-password", status_code=204)
def change_password(body: ChangePasswordIn, session=Depends(auth.session_user)) -> Response:
    """Allowed even while a password change is pending; ends the user's other sessions, keeps this one."""
    user, _ = session
    with _user_locks.setdefault(user.id, threading.Lock()):
        if not auth.verify_password(body.current_password, user.password_hash):
            raise DomainError("Current password is wrong", 403)
        if body.new_password == body.current_password:
            raise DomainError("The new password must differ from the current one", 422)
        auth.set_password(user, body.new_password, must_change=False)
        store.save_user(user)
    response = Response(status_code=204)
    auth.set_session_cookie(response, auth.issue_session(user)[0])
    return response
