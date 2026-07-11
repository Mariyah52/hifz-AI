from typing import Literal

from pydantic import EmailStr

from app.schemas.base import CamelModel

Role = Literal["student", "teacher", "parent", "admin"]


class RegisterRequest(CamelModel):
    email: EmailStr
    password: str
    name: str
    role: Role
    # Only meaningful when role == 'student'
    class_id: str | None = None
    # Only meaningful when role == 'parent'; links to an existing student on signup
    child_student_id: str | None = None

    # Phase 18 — every user belongs to an organization now:
    #  - role == 'admin': provide organization_name (+ optional
    #    organization_slug, defaulted from the name) to CREATE a brand
    #    new organization, becoming its first user.
    #  - any other role: provide organization_slug to JOIN an existing
    #    organization. Registration is rejected if the slug doesn't exist,
    #    or if the org's plan is already at its student/teacher limit.
    organization_slug: str | None = None
    organization_name: str | None = None


class LoginRequest(CamelModel):
    email: EmailStr
    password: str
    # Defaults True so any client that hasn't been updated to send this
    # (or a direct API caller) keeps getting the app's original
    # always-persistent-session behavior.
    stay_signed_in: bool = True


class TokenResponse(CamelModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: Role
    user_id: str
    name: str
    organization_slug: str


class RefreshRequest(CamelModel):
    refresh_token: str


class LogoutRequest(CamelModel):
    refresh_token: str


class RequestPasswordResetRequest(CamelModel):
    email: EmailStr


class ResetPasswordRequest(CamelModel):
    token: str
    new_password: str
