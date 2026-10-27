import threading

from fastapi import APIRouter, Depends

from app import auth, clock
from app.errors import DomainError
from app.models import User, UserCreateIn, UserPatchIn, UserRecord
from app.store import store

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(auth.require_role("admin"))])

# One lock so two admins cannot disable each other at the same moment (last-admin guard).
_lock = threading.Lock()


def _public(user: UserRecord) -> User:
    return User.model_validate(user.model_dump())


def _get(user_id: int) -> UserRecord:
    user = store.users.get(user_id)
    if user is None:
        raise DomainError("User not found", 404)
    return user


@router.get("")
def list_users() -> list[User]:
    return [_public(u) for u in sorted(store.users.values(), key=lambda u: u.id)]


@router.post("", status_code=201)
def create_user(body: UserCreateIn) -> User:
    with _lock:
        if store.get_user_by_name(body.username):
            raise DomainError("Username already exists", 409)
        user = UserRecord(
            id=store.next_user_id(), username=body.username, role=body.role,
            created_at=clock.now_utc(), password_hash=auth.hash_password(body.password),
        )
        store.save_user(user)
    return _public(user)


@router.patch("/{user_id}")
def update_user(user_id: int, body: UserPatchIn) -> User:
    with _lock:
        user = _get(user_id)
        active = user.active if body.active is None else body.active
        role = user.role if body.role is None else body.role
        if user.active and user.role == "admin" and (not active or role != "admin"):
            others = [u for u in store.users.values() if u.id != user.id and u.active and u.role == "admin"]
            if not others:
                raise DomainError("The last active administrator cannot be disabled or demoted", 409)
        if user.active and not active:
            user.session_version += 1  # ends the user's existing sessions at once
        if active:
            # re-enabling, or sending active=true to an active user, unlocks the account
            user.failed_attempts, user.locked_until = 0, None
        user.active, user.role = active, role
        store.save_user(user)
    return _public(user)
