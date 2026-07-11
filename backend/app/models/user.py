import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def today() -> date:
    return utcnow().date()


class User(Base):
    """
    One row per login, regardless of role. Role-specific data (streak,
    class membership, etc.) lives in the matching profile table below —
    a student always has exactly one StudentProfile, a teacher one
    TeacherProfile, and so on. Admins have no separate profile table;
    the `role` column alone is enough to grant admin access.

    `organization_id` (Phase 18) is the tenant boundary — every user
    belongs to exactly one organization, and every multi-user query
    (teacher rosters, admin lists/analytics, leaderboards) is scoped to
    the requester's own organization. See `app/models/organization.py`
    and `app/services/tenancy.py`.
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("u"))
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)  # 'student' | 'teacher' | 'parent' | 'admin'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    # Phase 17: account lockout after repeated failed logins — see
    # services/auth_security.py for the exact thresholds and logic.
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    student_profile: Mapped["StudentProfile"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    teacher_profile: Mapped["TeacherProfile"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    parent_profile: Mapped["ParentProfile"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("stu"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True)
    class_id: Mapped[str | None] = mapped_column(ForeignKey("classes.id"), nullable=True)

    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_active_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    freezes_available: Mapped[int] = mapped_column(Integer, default=2)

    user: Mapped["User"] = relationship(back_populates="student_profile")
    class_: Mapped["ClassRoom"] = relationship(back_populates="students")


class TeacherProfile(Base):
    __tablename__ = "teacher_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("t"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True)

    user: Mapped["User"] = relationship(back_populates="teacher_profile")
    classes: Mapped[list["ClassRoom"]] = relationship(back_populates="teacher")


class ParentProfile(Base):
    __tablename__ = "parent_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("p"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True)

    user: Mapped["User"] = relationship(back_populates="parent_profile")
