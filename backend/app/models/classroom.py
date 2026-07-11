from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import new_id


class ClassRoom(Base):
    __tablename__ = "classes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("c"))
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String)
    teacher_id: Mapped[str | None] = mapped_column(ForeignKey("teacher_profiles.id"), nullable=True)

    teacher: Mapped["TeacherProfile"] = relationship(back_populates="classes")  # noqa: F821
    students: Mapped[list["StudentProfile"]] = relationship(back_populates="class_")  # noqa: F821


class ParentChildLink(Base):
    """
    The real version of the link `parentService.ts` used to hardcode on
    the frontend (Phase 8's `LINKED_CHILD_STUDENT_ID`). One parent can be
    linked to more than one child; a child can (in principle) have more
    than one linked parent.
    """

    __tablename__ = "parent_child_links"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("pcl"))
    parent_id: Mapped[str] = mapped_column(ForeignKey("parent_profiles.id"))
    student_id: Mapped[str] = mapped_column(ForeignKey("student_profiles.id"))
