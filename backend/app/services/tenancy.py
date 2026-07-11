import re

from sqlalchemy.orm import Session

from app.models.organization import PLAN_DEFAULTS, Organization
from app.models.user import User

_SLUG_SANITIZE_RE = re.compile(r"[^a-z0-9-]+")


class PlanLimitExceeded(Exception):
    pass


class SlugTaken(Exception):
    pass


def normalize_slug(raw: str) -> str:
    lowered = raw.strip().lower().replace(" ", "-")
    return _SLUG_SANITIZE_RE.sub("", lowered)


def get_organization_by_slug(db: Session, slug: str) -> Organization | None:
    return db.query(Organization).filter(Organization.slug == normalize_slug(slug)).first()


def create_organization(db: Session, name: str, slug: str, plan: str = "free") -> Organization:
    normalized = normalize_slug(slug)
    if get_organization_by_slug(db, normalized) is not None:
        raise SlugTaken(f"An organization with slug '{normalized}' already exists")

    limits = PLAN_DEFAULTS.get(plan, PLAN_DEFAULTS["free"])
    organization = Organization(
        name=name, slug=normalized, plan=plan,
        max_students=limits["max_students"], max_teachers=limits["max_teachers"],
    )
    db.add(organization)
    db.flush()
    return organization


def count_users_by_role(db: Session, organization_id: str, role: str) -> int:
    return db.query(User).filter(User.organization_id == organization_id, User.role == role).count()


def enforce_plan_limit(db: Session, organization: Organization, role: str) -> None:
    """
    Raises PlanLimitExceeded if adding one more user of this role would
    put the organization over its plan's limit. Only 'student' and
    'teacher' are capped — parents and admins aren't a capacity concern
    the same way (a school pays per student/teacher seat, not per parent
    watching one).
    """
    if role == "student" and count_users_by_role(db, organization.id, "student") >= organization.max_students:
        raise PlanLimitExceeded(
            f"This organization's {organization.plan} plan allows up to "
            f"{organization.max_students} students. Ask an admin to upgrade the plan."
        )
    if role == "teacher" and count_users_by_role(db, organization.id, "teacher") >= organization.max_teachers:
        raise PlanLimitExceeded(
            f"This organization's {organization.plan} plan allows up to "
            f"{organization.max_teachers} teachers. Ask an admin to upgrade the plan."
        )
