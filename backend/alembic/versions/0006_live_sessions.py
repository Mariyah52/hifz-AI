"""live session tables

Revision ID: 0006_live_sessions
Revises: 0005_offline_sync
Create Date: 2026-07-08

Phase 25: live_sessions, live_session_participants (real automatic
attendance via join/leave timestamps), and live_session_mistakes.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006_live_sessions"
down_revision: Union[str, None] = "0005_offline_sync"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "live_sessions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("class_id", sa.String(), sa.ForeignKey("classes.id"), nullable=False),
        sa.Column("teacher_id", sa.String(), sa.ForeignKey("teacher_profiles.id"), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="live"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_live_sessions_class_id", "live_sessions", ["class_id"])
    op.create_index("ix_live_sessions_teacher_id", "live_sessions", ["teacher_id"])

    op.create_table(
        "live_session_participants",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("session_id", sa.String(), sa.ForeignKey("live_sessions.id"), nullable=False),
        sa.Column("student_id", sa.String(), sa.ForeignKey("student_profiles.id"), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("left_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_live_session_participants_session_id", "live_session_participants", ["session_id"])
    op.create_index("ix_live_session_participants_student_id", "live_session_participants", ["student_id"])

    op.create_table(
        "live_session_mistakes",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("session_id", sa.String(), sa.ForeignKey("live_sessions.id"), nullable=False),
        sa.Column("student_id", sa.String(), sa.ForeignKey("student_profiles.id"), nullable=False),
        sa.Column("mark_type", sa.String(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_live_session_mistakes_session_id", "live_session_mistakes", ["session_id"])
    op.create_index("ix_live_session_mistakes_student_id", "live_session_mistakes", ["student_id"])


def downgrade() -> None:
    op.drop_table("live_session_mistakes")
    op.drop_table("live_session_participants")
    op.drop_table("live_sessions")
