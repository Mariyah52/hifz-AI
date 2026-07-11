"""AI-based test analysis, replacing self-report

Revision ID: 0011_ai_test_analysis
Revises: 0010_api_keys
Create Date: 2026-07-11

Test Mode switches from student self-marking to the same real recitation
analysis Phase 14 built for Practice Mode: one continuous recording across
the whole ayah range, transcribed once (Whisper) and word-diffed against
the real reference text. `test_results.self_mark` (student-reported) is
renamed to `mark` (now AI-derived from the diff) so the column name
doesn't keep implying something no longer true; `matched_word_count`/
`total_word_count` carry the real per-ayah tally behind that mark, and
`test_mistakes` mirrors `practice_mistakes` exactly. Per-ayah
`duration_seconds` is dropped — a continuous recording only has one
overall duration, not a per-ayah one; the recording itself is kept via
`test_sessions.audio_url`.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0011_ai_test_analysis"
down_revision: Union[str, None] = "0010_api_keys"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("test_sessions") as batch_op:
        batch_op.add_column(sa.Column("audio_url", sa.String(), nullable=True))
        batch_op.add_column(
            sa.Column("analysis_status", sa.String(), nullable=False, server_default="completed")
        )
        batch_op.add_column(sa.Column("analysis_error", sa.Text(), nullable=True))

    with op.batch_alter_table("test_results") as batch_op:
        batch_op.alter_column("self_mark", new_column_name="mark", existing_type=sa.String())
        batch_op.add_column(sa.Column("matched_word_count", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("total_word_count", sa.Integer(), nullable=False, server_default="0"))
        batch_op.drop_column("duration_seconds")

    op.create_table(
        "test_mistakes",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("session_id", sa.String(), sa.ForeignKey("test_sessions.id"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("mistake_type", sa.String(), nullable=False),
        sa.Column("ayah_number", sa.Integer(), nullable=True),
        sa.Column("reference_word", sa.String(), nullable=True),
        sa.Column("transcribed_word", sa.String(), nullable=True),
    )
    op.create_index("ix_test_mistakes_session_id", "test_mistakes", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_test_mistakes_session_id", table_name="test_mistakes")
    op.drop_table("test_mistakes")

    with op.batch_alter_table("test_results") as batch_op:
        batch_op.add_column(sa.Column("duration_seconds", sa.Float(), nullable=False, server_default="0"))
        batch_op.drop_column("total_word_count")
        batch_op.drop_column("matched_word_count")
        batch_op.alter_column("mark", new_column_name="self_mark", existing_type=sa.String())

    with op.batch_alter_table("test_sessions") as batch_op:
        batch_op.drop_column("analysis_error")
        batch_op.drop_column("analysis_status")
        batch_op.drop_column("audio_url")
