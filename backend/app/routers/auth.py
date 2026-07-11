from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.classroom import ClassRoom, ParentChildLink
from app.models.organization import Organization
from app.models.user import ParentProfile, StudentProfile, TeacherProfile, User
from app.rate_limit import limiter
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    RequestPasswordResetRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.security import create_access_token, hash_password, verify_password
from app.services.auth_security import (
    consume_password_reset_token,
    is_account_locked,
    issue_password_reset_token,
    issue_refresh_token,
    log_audit_event,
    register_failed_login,
    register_successful_login,
    revoke_all_refresh_tokens_for_user,
    revoke_refresh_token,
    verify_password_reset_token,
    verify_refresh_token,
)
from app.services.email_service import send_email
from app.services.tenancy import PlanLimitExceeded, SlugTaken, create_organization, enforce_plan_limit, get_organization_by_slug

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _issue_token_pair(db: Session, user: User, long_lived: bool = True) -> TokenResponse:
    access_token = create_access_token(subject=user.id, role=user.role)
    refresh_token = issue_refresh_token(db, user.id, long_lived=long_lived)
    organization = db.get(Organization, user.organization_id)
    return TokenResponse(
        access_token=access_token, refresh_token=refresh_token, role=user.role, user_id=user.id,
        name=user.name, organization_slug=organization.slug if organization else "",
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
def register(request: Request, payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")

    # --- Phase 18: resolve which organization this user belongs to -----
    # An admin signing up creates a brand new organization (the "start
    # using HifzAI for my institution" flow); every other role must join
    # an existing one by slug (the "my school already uses this" flow).
    if payload.role == "admin":
        if not payload.organization_name:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "organizationName is required when registering as an admin"
            )
        try:
            organization = create_organization(
                db, name=payload.organization_name, slug=payload.organization_slug or payload.organization_name
            )
        except SlugTaken as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    else:
        if not payload.organization_slug:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "organizationSlug is required to join an existing organization"
            )
        organization = get_organization_by_slug(db, payload.organization_slug)
        if organization is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "No organization found with that slug")
        try:
            enforce_plan_limit(db, organization, payload.role)
        except PlanLimitExceeded as exc:
            raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, str(exc)) from exc

    user = User(
        organization_id=organization.id,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        name=payload.name,
        role=payload.role,
    )
    db.add(user)
    db.flush()  # assigns user.id without committing yet

    if payload.role == "student":
        class_id = payload.class_id
        if class_id is not None:
            # A student can only join a class that belongs to the SAME
            # organization — without this check, a student could enroll
            # into another institution's class by guessing its id.
            class_room = db.get(ClassRoom, class_id)
            if class_room is None or class_room.organization_id != organization.id:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "class_id does not exist in this organization")
        db.add(StudentProfile(user_id=user.id, class_id=class_id))
    elif payload.role == "teacher":
        db.add(TeacherProfile(user_id=user.id))
    elif payload.role == "parent":
        parent_profile = ParentProfile(user_id=user.id)
        db.add(parent_profile)
        db.flush()
        if payload.child_student_id:
            student = db.get(StudentProfile, payload.child_student_id)
            # Same cross-tenant guard: a parent can only link to a child
            # in their own organization, checked via the child's user row.
            student_user = db.get(User, student.user_id) if student else None
            if student is None or student_user is None or student_user.organization_id != organization.id:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "child_student_id does not exist in this organization")
            db.add(ParentChildLink(parent_id=parent_profile.id, student_id=student.id))
    # 'admin' needs no profile row — the role on `users` is sufficient.

    db.commit()
    log_audit_event(
        db, "register", user_id=user.id, ip_address=_client_ip(request), detail=f"org={organization.slug}"
    )

    return _issue_token_pair(db, user)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email).first()

    if user is not None and is_account_locked(user):
        log_audit_event(db, "login_blocked_locked", user_id=user.id, ip_address=_client_ip(request))
        raise HTTPException(
            status.HTTP_423_LOCKED,
            "This account is temporarily locked after too many failed login attempts. Try again later.",
        )

    if user is None or not verify_password(payload.password, user.hashed_password):
        if user is not None:
            register_failed_login(db, user)
        log_audit_event(
            db, "login_failure", user_id=user.id if user else None, ip_address=_client_ip(request),
            detail=payload.email,
        )
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")

    register_successful_login(db, user)
    log_audit_event(db, "login_success", user_id=user.id, ip_address=_client_ip(request))

    return _issue_token_pair(db, user, long_lived=payload.stay_signed_in)


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: Request, payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """
    Refresh-token rotation: the presented token is revoked and a new one
    issued alongside the new access token, rather than reusing the same
    refresh token indefinitely — limits how long a stolen refresh token
    stays useful if it's ever leaked without being noticed immediately.
    """
    token = verify_refresh_token(db, payload.refresh_token)
    if token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")

    user = db.get(User, token.user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User no longer exists")

    long_lived = token.long_lived
    revoke_refresh_token(db, token)
    log_audit_event(db, "token_refresh", user_id=user.id, ip_address=_client_ip(request))

    # Carries forward the "stay signed in" choice made at the original
    # login — a rotated refresh token shouldn't silently switch from a
    # short session to a 30-day one (or vice versa).
    return _issue_token_pair(db, user, long_lived=long_lived)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, payload: LogoutRequest, db: Session = Depends(get_db)) -> None:
    token = verify_refresh_token(db, payload.refresh_token)
    if token is not None:
        revoke_refresh_token(db, token)
        log_audit_event(db, "logout", user_id=token.user_id, ip_address=_client_ip(request))
    # No error if the token was already invalid/missing — logging out of an
    # already-invalid session should still succeed from the client's view.


@router.post("/request-password-reset", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("3/minute")
def request_password_reset(
    request: Request, payload: RequestPasswordResetRequest, db: Session = Depends(get_db)
) -> None:
    """
    Always returns 204 regardless of whether the email exists — revealing
    that would let an attacker enumerate registered accounts. The reset
    email is only actually sent if a matching user exists; otherwise this
    silently does nothing.
    """
    user = db.query(User).filter(User.email == payload.email).first()
    if user is not None:
        raw_token = issue_password_reset_token(db, user.id)
        reset_link = f"{settings.frontend_url}/reset-password?token={raw_token}"
        send_email(
            user.email,
            "Reset your HifzAI password",
            f"Someone requested a password reset for this account. If that was you, use this link "
            f"within 30 minutes: {reset_link}\n\nIf it wasn't you, you can ignore this email.",
        )
        log_audit_event(db, "password_reset_requested", user_id=user.id, ip_address=_client_ip(request))


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(request: Request, payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> None:
    token = verify_password_reset_token(db, payload.token)
    if token is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired reset link")

    user = db.get(User, token.user_id)
    if user is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired reset link")

    user.hashed_password = hash_password(payload.new_password)
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()

    consume_password_reset_token(db, token)
    # A password reset invalidates every existing session — if the reset
    # was needed because of a compromised password, any refresh token
    # obtained under the old password shouldn't still work.
    revoke_all_refresh_tokens_for_user(db, user.id)
    log_audit_event(db, "password_reset_completed", user_id=user.id, ip_address=_client_ip(request))
