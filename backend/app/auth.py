import secrets
import time
from threading import BoundedSemaphore

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, SecretStr
from sqlalchemy import delete, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import (
    SESSION_SECONDS, IDLE_SECONDS, LoginLimit, Staff, StaffSession,
    audit, check_origin, dummy_password_hash, require_staff, settings,
    staff_view, token_hash, verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["Staff authentication"])
password_slots = BoundedSemaphore(2)


class Login(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=1, max_length=64)
    password: SecretStr = Field(min_length=1, max_length=128)


def throttle(db, username, ip):
    now = int(time.time())
    # Atomic counters shared by all workers using this SQLite database.
    db.execute(delete(LoginLimit).where(LoginLimit.window_start < now - 900))
    blocked = False
    for label, value, maximum in (("account", username, 5), ("ip", ip, 30)):
        key = token_hash(label + ":" + value)
        statement = insert(LoginLimit).values(key=key, attempts=1, window_start=now)
        statement = statement.on_conflict_do_update(index_elements=[LoginLimit.key], set_={"attempts": LoginLimit.attempts + 1})
        db.execute(statement)
        count = db.scalar(select(LoginLimit.attempts).where(LoginLimit.key == key))
        blocked |= count > maximum
    db.commit()
    if blocked:
        raise HTTPException(429, "Too many sign-in attempts. Try again in 15 minutes", headers={"Retry-After": "900"})


@router.post("/login")
def login(payload: Login, request: Request, response: Response, db: Session = Depends(get_db)):
    check_origin(request)
    username = payload.username.strip().lower()
    throttle(db, username, request.client.host if request.client else "unknown")
    staff = db.scalar(select(Staff).where(Staff.username == username))
    if not password_slots.acquire(blocking=False):
        raise HTTPException(429, "Sign-in service is busy. Try again shortly", headers={"Retry-After": "2"})
    try:
        credential = staff.password_hash if staff else dummy_password_hash()
        valid = verify_password(payload.password.get_secret_value(), credential)
    finally:
        password_slots.release()
    if staff is not None:
        db.refresh(staff)
        valid = valid and secrets.compare_digest(staff.password_hash, credential)
    if not valid or staff is None or not staff.active or staff.role not in {"admin", "cashier", "operations"}:
        audit(db, staff.id if staff else None, "login_failed")
        db.commit()
        raise HTTPException(401, "Invalid username or password")
    now = int(time.time())
    # Reauthentication rotates and invalidates the presented session.
    old_token = request.cookies.get(settings().cookie_name, "")
    db.execute(delete(StaffSession).where(StaffSession.token_hash == token_hash(old_token)))
    db.execute(delete(StaffSession).where((StaffSession.expires_at <= now) | (StaffSession.last_seen <= now - IDLE_SECONDS)))
    existing = db.scalars(select(StaffSession).where(StaffSession.staff_id == staff.id).order_by(StaffSession.last_seen.desc())).all()
    for stale in existing[4:]:
        db.delete(stale)
    token = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(32)
    db.add(StaffSession(token_hash=token_hash(token), staff_id=staff.id, csrf_token=csrf,
                        expires_at=now + SESSION_SECONDS, last_seen=now))
    db.execute(delete(LoginLimit).where(LoginLimit.key == token_hash("account:" + username)))
    audit(db, staff.id, "login_success")
    db.commit()
    response.set_cookie(settings().cookie_name, token, max_age=SESSION_SECONDS,
                        httponly=True, secure=settings().production, samesite="strict", path="/")
    return {"staff": staff_view(staff), "csrf_token": csrf}


@router.get("/me")
def me(request: Request, staff: Staff = Depends(require_staff)):
    return {"staff": staff_view(staff), "csrf_token": request.state.staff_session.csrf_token}


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(get_db), staff: Staff = Depends(require_staff)):
    db.execute(delete(StaffSession).where(StaffSession.token_hash == request.state.staff_session.token_hash))
    audit(db, staff.id, "logout")
    db.commit()
    response.delete_cookie(settings().cookie_name, path="/", httponly=True,
                           secure=settings().production, samesite="strict")
