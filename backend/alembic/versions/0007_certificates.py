"""certificates table

Revision ID: 0007_certificates
Revises: 0006_live_sessions
Create Date: 2026-07-08

Phase 27: surah/juz completion (auto-detected) and attendance/competition
(teacher/admin-issued) certificates. PDFs are rendered on demand, never stored.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0007_certificates"
down_revision: Union[str, None] = "0006_live_sessions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "certificates",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("student_id", sa.String(), sa.ForeignKey("student_profiles.id"), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("issued_by_teacher_id", sa.String(), sa.ForeignKey("teacher_profiles.id"), nullable=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_certificates_student_id", "certificates", ["student_id"])


def downgrade() -> None:
    op.drop_table("certificates")
