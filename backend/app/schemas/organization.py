from app.schemas.base import CamelModel


class OrganizationPublicOut(CamelModel):
    """What an unauthenticated visitor can see before logging in — just enough for a branded login page."""

    name: str
    slug: str
    primary_color: str | None
    secondary_color: str | None
    logo_url: str | None
    welcome_message: str | None


class OrganizationAdminOut(CamelModel):
    """The admin's own organization, including plan usage — real numbers, not placeholders."""

    id: str
    name: str
    slug: str
    plan: str
    max_students: int
    max_teachers: int
    current_student_count: int
    current_teacher_count: int
    primary_color: str | None
    secondary_color: str | None
    logo_url: str | None
    welcome_message: str | None
    principal_message: str | None


class UpdateOrganizationRequest(CamelModel):
    name: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    logo_url: str | None = None
    welcome_message: str | None = None
    principal_message: str | None = None
