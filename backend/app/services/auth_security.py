import hashlib
import secrets
from datetime import timedelta

from sqlalchemy.orm import Session

from app.config import settings
from app.models.auth_security import AuditLogEntry, PasswordResetToken, RefreshToken
from app.models.user import User, utcnow


def _hash_token(raw_token: str) -> str:
    """
    SHA-256 is fine here (unlike password hashing, which needs bcrypt's
    deliberate slowness) — these are high-entropy random tokens, not
    human-guessable passwords, so there's no brute-force risk to slow
    down against. The point of hashing at all is just "don't store the
    literal bearer token in the database."
    """
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


# --- Refresh tokens ------------------------------------------------------


def issue_refresh_token(db: Session, user_id: str, long_lived: bool = True) -> str:
    raw_token = secrets.token_urlsafe(48)
    expire_days = settings.refresh_token_expire_days if long_lived else settings.short_refresh_token_expire_days
    db.add(
        RefreshToken(
            user_id=user_id,
            token_hash=_hash_token(raw_token),
            expires_at=utcnow() + timedelta(days=expire_days),
            long_lived=long_lived,
        )
    )
    db.commit()
    return raw_token


def verify_refresh_token(db: Session, raw_token: str) -> RefreshToken | None:
    token = db.query(RefreshToken).filter(RefreshToken.token_hash == _hash_token(raw_token)).first()
    if token is None or token.revoked_at is not None or token.expires_at < utcnow():
        return None
    return token


def revoke_refresh_token(db: Session, token: RefreshToken) -> None:
    token.revoked_at = utcnow()
    db.commit()


def revoke_all_refresh_tokens_for_user(db: Session, user_id: str) -> None:
    db.query(RefreshToken).filter(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)).update(
        {"revoked_at": utcnow()}
    )
    db.commit()


# --- Password reset --------------------------------------------------------


def issue_password_reset_token(db: Session, user_id: str) -> str:
    raw_token = secrets.token_urlsafe(32)
    db.add(
        PasswordResetToken(
            user_id=user_id,
            token_hash=_hash_token(raw_token),
            expires_at=utcnow() + timedelta(minutes=settings.password_reset_token_expire_minutes),
        )
    )
    db.commit()
    return raw_token


def verify_password_reset_token(db: Session, raw_token: str) -> PasswordResetToken | None:
    token = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == _hash_token(raw_token)).first()
    if token is None or token.used_at is not None or token.expires_at < utcnow():
        return None
    return token


def consume_password_reset_token(db: Session, token: PasswordResetToken) -> None:
    token.used_at = utcnow()
    db.commit()


# --- Account lockout --------------------------------------------------------


def is_account_locked(user: User) -> bool:
    return user.locked_until is not None and user.locked_until > utcnow()


def register_failed_login(db: Session, user: User) -> None:
    user.failed_login_attempts += 1
    if user.failed_login_attempts >= settings.max_failed_login_attempts:
        user.locked_until = utcnow() + timedelta(minutes=settings.account_lockout_minutes)
    db.commit()


def register_successful_login(db: Session, user: User) -> None:
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()


# --- Audit log --------------------------------------------------------------


def log_audit_event(
    db: Session, action: str, user_id: str | None = None, ip_address: str | None = None, detail: str | None = None
) -> None:
    db.add(AuditLogEntry(user_id=user_id, action=action, ip_address=ip_address, detail=detail))
    db.commit()
