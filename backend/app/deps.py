from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.api_access import ApiKey
from app.models.user import ParentProfile, StudentProfile, TeacherProfile, User
from app.security import decode_access_token
from app.services.api_key_service import authenticate as authenticate_api_key

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Phase 30: the public integration API authenticates via a header, not a
# JWT — `auto_error=False` so a missing header falls through to our own
# 401 with a clearer message instead of FastAPI's default.
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token") from exc

    user = db.get(User, payload.get("sub"))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User no longer exists")
    return user


def require_role(*roles: str):
    def _check(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"This endpoint requires role: {', '.join(roles)}")
        return user

    return _check


def get_current_student_profile(
    user: User = Depends(require_role("student")), db: Session = Depends(get_db)
) -> StudentProfile:
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student profile not found")
    return profile


def get_current_teacher_profile(
    user: User = Depends(require_role("teacher")), db: Session = Depends(get_db)
) -> TeacherProfile:
    profile = db.query(TeacherProfile).filter(TeacherProfile.user_id == user.id).first()
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Teacher profile not found")
    return profile


def get_current_parent_profile(
    user: User = Depends(require_role("parent")), db: Session = Depends(get_db)
) -> ParentProfile:
    profile = db.query(ParentProfile).filter(ParentProfile.user_id == user.id).first()
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Parent profile not found")
    return profile


def get_api_key(raw_key: str | None = Depends(api_key_header), db: Session = Depends(get_db)) -> ApiKey:
    """
    Phase 30: the public API's equivalent of `get_current_user` — every
    `/v1/*` endpoint depends on this instead of a JWT. Resolves to the
    `ApiKey` row so routers can scope every query to `api_key.organization_id`,
    the exact same tenant-boundary pattern the admin router already uses
    with `admin.organization_id`.
    """
    if not raw_key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing X-API-Key header")
    key = authenticate_api_key(db, raw_key)
    if key is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or revoked API key")
    return key


def require_api_scope(scope: str):
    """
    Phase 31: layers on top of get_api_key for endpoints that mutate
    data. Every key defaults to 'read' scope (see ApiKey model) — a key
    issued before write endpoints existed, or one an admin deliberately
    keeps read-only, gets a 403 here rather than silently being allowed
    to write once the endpoint existed.
    """
    def _check(api_key: ApiKey = Depends(get_api_key)) -> ApiKey:
        if not api_key.has_scope(scope):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"This API key doesn't have '{scope}' scope. Ask an admin to issue a key with write access.",
            )
        return api_key

    return _check
