"""Staff credentials, revocable sessions, and deny-by-default authorization."""
import hashlib
import hmac
import os
import re
import secrets
import time
from dataclasses import dataclass
from functools import lru_cache
from urllib.parse import urlsplit

from fastapi import Depends, HTTPException, Request
from sqlalchemy import Boolean, ForeignKey, Integer, String, delete, select, update
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.database import Base, get_db

ROLES = {"admin", "cashier", "operations"}
SESSION_SECONDS = 8 * 60 * 60
IDLE_SECONDS = 30 * 60


@dataclass(frozen=True)
class Settings:
    production: bool
    origins: tuple[str, ...]
    hosts: tuple[str, ...]

    @property
    def cookie_name(self):
        return "__Host-kg_session" if self.production else "kg_session"


@dataclass(frozen=True)
class SessionContext:
    token_hash: str
    csrf_token: str


@lru_cache
def settings():
    environment = os.environ.get("KG_ENV", "development")
    if environment not in {"development", "production"}:
        raise RuntimeError("KG_ENV must be development or production")
    production = environment == "production"
    origins = tuple(x.strip() for x in os.environ.get(
        "KG_ALLOWED_ORIGINS", "" if production else "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",") if x.strip())
    if not origins:
        raise RuntimeError("KG_ALLOWED_ORIGINS must contain the exact frontend origin")
    hosts = set()
    for origin in origins:
        url = urlsplit(origin)
        if (url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password
                or url.path or url.query or url.fragment or "*" in origin
                or (production and url.scheme != "https")
                or (not production and url.hostname not in {"localhost", "127.0.0.1", "::1"})):
            raise RuntimeError("Use exact HTTPS origins in production, or loopback origins in development")
        hosts.add(url.hostname)
    if not production:
        hosts.update({"localhost", "127.0.0.1", "::1"})
    return Settings(production, origins, tuple(sorted(hosts)))


class Staff(Base):
    __tablename__ = "staff"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class StaffSession(Base):
    __tablename__ = "staff_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    staff_id: Mapped[int] = mapped_column(ForeignKey("staff.id"), index=True)
    csrf_token: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[int] = mapped_column(Integer, index=True)
    last_seen: Mapped[int] = mapped_column(Integer, nullable=False)


class LoginLimit(Base):
    __tablename__ = "login_limits"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    window_start: Mapped[int] = mapped_column(Integer, index=True)


class AuditEvent(Base):
    __tablename__ = "staff_audit_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    staff_id: Mapped[int | None] = mapped_column(ForeignKey("staff.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[int] = mapped_column(Integer, default=lambda: int(time.time()), index=True)


def initialize_security(engine):
    # Additive only: existing customer/order/payment tables and data are untouched.
    Base.metadata.create_all(engine, tables=[Staff.__table__, StaffSession.__table__, LoginLimit.__table__, AuditEvent.__table__])
    dummy_password_hash()


def username_key(value):
    value = value.strip().lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9_.-]{2,63}", value):
        raise ValueError("Username must be 3–64 letters, digits, dots, underscores or hyphens")
    return value


def token_hash(value):
    return hashlib.sha256(value.encode()).hexdigest()


def hash_password(password):
    if not 15 <= len(password) <= 128 or not password.strip():
        raise ValueError("Use a unique passphrase of 15–128 characters")
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**17, r=8, p=1, maxmem=256 * 1024 * 1024)
    return f"scrypt$131072$8$1${salt.hex()}${digest.hex()}"


def verify_password(password, encoded):
    try:
        algorithm, n, r, p, salt, expected = encoded.split("$")
        if (algorithm, n, r, p) != ("scrypt", "131072", "8", "1"):
            return False
        digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=2**17, r=8, p=1, maxmem=256 * 1024 * 1024)
        return hmac.compare_digest(digest.hex(), expected)
    except (ValueError, TypeError):
        return False


# Equal-cost verification for unknown users; no usable default account/credential.
@lru_cache
def dummy_password_hash():
    return hash_password(secrets.token_urlsafe(48))


def audit(db, staff_id, action, resource_id=None):
    db.add(AuditEvent(staff_id=staff_id, action=action, resource_id=resource_id))


def check_origin(request):
    if request.headers.get("origin") not in settings().origins:
        raise HTTPException(403, "Request origin is not allowed")


def require_staff(request: Request, db: Session = Depends(get_db)):
    # Explicit public allowlist; all new application routes are protected by default.
    if (request.method, request.url.path) in {("GET", "/health"), ("POST", "/api/auth/login")}:
        return None
    token = request.cookies.get(settings().cookie_name, "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{43}", token):
        raise HTTPException(401, "Staff sign-in required")
    session = db.get(StaffSession, token_hash(token))
    now = int(time.time())
    if session is None or session.expires_at <= now or session.last_seen <= now - IDLE_SECONDS:
        raise HTTPException(401, "Session expired. Please sign in again")
    staff = db.get(Staff, session.staff_id)
    if staff is None or not staff.active or staff.role not in ROLES:
        raise HTTPException(401, "Staff sign-in required")
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        check_origin(request)
        if not hmac.compare_digest(request.headers.get("x-csrf-token", "").encode(), session.csrf_token.encode()):
            raise HTTPException(403, "Invalid CSRF token. Refresh and try again")
    # A short separate commit releases SQLite read locks before business writes.
    context = SessionContext(session.token_hash, session.csrf_token)
    changed = db.execute(update(StaffSession).where(StaffSession.token_hash == context.token_hash).values(last_seen=now))
    if changed.rowcount != 1:
        db.rollback()
        raise HTTPException(401, "Session revoked. Please sign in again")
    db.commit()
    request.state.staff_session = context
    request.state.staff = staff
    return staff


def require_payment_staff(staff: Staff = Depends(require_staff)):
    if staff is None or staff.role not in {"admin", "cashier"}:
        raise HTTPException(403, "Payment recording requires a cashier or administrator")
    return staff


def revoke_staff_sessions(db, staff_id):
    db.execute(delete(StaffSession).where(StaffSession.staff_id == staff_id))


def staff_view(staff):
    return {"id": staff.id, "username": staff.username, "role": staff.role,
            "can_record_payments": staff.role in {"admin", "cashier"}}
