from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.user import new_id, utcnow


class RefreshToken(Base):
    """
    One row per issued refresh token. Only the SHA-256 hash is stored —
    never the raw token — so a database leak alone can't be used to
    forge sessions (same principle as password hashing, applied to
    tokens). `revoked_at` set means "no longer usable," whether from an
    explicit logout, rotation on refresh, or a password reset (which
    revokes every refresh token for that user — see routers/auth.py).
    """

    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("rtk"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    # "Stay signed in" at login (see routers/auth.py). True = the normal
    # `refresh_token_expire_days` (30) lifetime, kept in the frontend's
    # localStorage. False = `short_refresh_token_expire_days`, kept in
    # sessionStorage instead so it's gone the moment the browser closes.
    # Carried forward unchanged every time this token is rotated on
    # /auth/refresh, so the choice sticks for the life of the session.
    long_lived: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")


class PasswordResetToken(Base):
    """
    Same hash-only-storage principle as RefreshToken. `used_at` prevents
    replay (a reset link can only ever be consumed once); expiry is
    short (see services/auth_security.py) since this grants account
    takeover if it leaks.
    """

    __tablename__ = "password_reset_tokens"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("prt"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AuditLogEntry(Base):
    """
    Append-only security audit trail. `user_id` is nullable because some
    events (a failed login with an email that doesn't exist) have no
    real user to attribute them to — recording "someone tried this email"
    is still useful, inventing a user_id for it would not be.
    """

    __tablename__ = "audit_log_entries"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("aud"))
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String, index=True)
    ip_address: Mapped[str | None] = mapped_column(String, nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
