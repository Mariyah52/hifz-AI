from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import new_id, utcnow


class LiveSession(Base):
    """
    One row per live class a teacher starts. `status` moves
    'scheduled' (not used yet — sessions start live today, no advance
    scheduling UI was built) -> 'live' -> 'ended'. Real-time audio itself
    is peer-to-peer WebRTC between browsers (see the
    `/ws/live-sessions/{id}` signaling endpoint); this row and its
    children are the durable record of what happened.
    """

    __tablename__ = "live_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("live"))
    class_id: Mapped[str] = mapped_column(ForeignKey("classes.id"), index=True)
    teacher_id: Mapped[str] = mapped_column(ForeignKey("teacher_profiles.id"), index=True)
    status: Mapped[str] = mapped_column(String, default="live")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    class_room: Mapped["ClassRoom"] = relationship()  # noqa: F821
    teacher: Mapped["TeacherProfile"] = relationship()  # noqa: F821


class LiveSessionParticipant(Base):
    """
    Real, automatic attendance: a row is created the moment a student's
    browser actually establishes the WebSocket connection to join (not
    when they merely see a "join" button), and `left_at` is set the
    moment that connection closes — whether they tapped leave or just
    lost connectivity.
    """

    __tablename__ = "live_session_participants"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("livepart"))
    session_id: Mapped[str] = mapped_column(ForeignKey("live_sessions.id"), index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("student_profiles.id"), index=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    student: Mapped["StudentProfile"] = relationship()  # noqa: F821


class LiveSessionMistake(Base):
    """
    A mark the teacher made live, during a specific student's turn — the
    real-time equivalent of Test Mode's self-marking, except here the
    teacher is the one judging, live, same as an in-person halaqah.
    """

    __tablename__ = "live_session_mistakes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("livemistake"))
    session_id: Mapped[str] = mapped_column(ForeignKey("live_sessions.id"), index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("student_profiles.id"), index=True)
    mark_type: Mapped[str] = mapped_column(String)  # 'perfect' | 'hesitation' | 'mistake'
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    student: Mapped["StudentProfile"] = relationship()  # noqa: F821
