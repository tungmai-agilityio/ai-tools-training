import threading
from datetime import timedelta

from fastapi import APIRouter, Depends, Request, Response

from app import auth, clock, config
from app.errors import DomainError
from app.models import LoginIn, SessionOut, UserRecord
from app.store import store

router = APIRouter(prefix="/auth", tags=["auth"])

# ponytail: one global lock makes check, verify and counter update atomic so parallel guesses cannot
# skip the lockout; serialises logins (~50 ms each), use per-username locks if login volume grows.
_login_lock = threading.Lock()


def _session_out(user: UserRecord, expires) -> SessionOut:
    return SessionOut(username=user.username, role=user.role, expires_at=expires, must_change_password=user.must_change_password)


@router.post("/login")
def login(body: LoginIn, response: Response) -> SessionOut:
    if not config.AUTH_SECRET:
        raise DomainError("Login is not configured", 503)
    with _login_lock:
        return _login(body, response)


def _login(body: LoginIn, response: Response) -> SessionOut:
    now = clock.now_utc()
    user = store.get_user_by_name(body.username)
    if user and user.locked_until and now < user.locked_until:
        raise DomainError("Too many failed attempts. Try again later.", 423)
    if user is None or not user.active:
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
