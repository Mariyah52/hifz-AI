"""notes table + offline-sync idempotency columns

Revision ID: 0005_offline_sync
Revises: 0004_chat_tables
Create Date: 2026-07-08

Phase 26: a `notes` table, plus `client_mutation_id` on practice_attempts
and test_sessions so a retried offline-queue sync never creates a
duplicate row.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005_offline_sync"
down_revision: Union[str, None] = "0004_chat_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("practice_attempts") as batch_op:
        batch_op.add_column(sa.Column("client_mutation_id", sa.String(), nullable=True))
        batch_op.create_unique_constraint("uq_practice_attempts_client_mutation_id", ["client_mutation_id"])

    with op.batch_alter_table("test_sessions") as batch_op:
        batch_op.add_column(sa.Column("client_mutation_id", sa.String(), nullable=True))
        batch_op.create_unique_constraint("uq_test_sessions_client_mutation_id", ["client_mutation_id"])

    op.create_table(
        "notes",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("student_id", sa.String(), sa.ForeignKey("student_profiles.id"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("surah_number", sa.Integer(), nullable=True),
        sa.Column("ayah_number", sa.Integer(), nullable=True),
        sa.Column("client_mutation_id", sa.String(), nullable=True, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_notes_student_id", "notes", ["student_id"])


def downgrade() -> None:
    op.drop_table("notes")
    with op.batch_alter_table("test_sessions") as batch_op:
        batch_op.drop_constraint("uq_test_sessions_client_mutation_id", type_="unique")
        batch_op.drop_column("client_mutation_id")
    with op.batch_alter_table("practice_attempts") as batch_op:
        batch_op.drop_constraint("uq_practice_attempts_client_mutation_id", type_="unique")
        batch_op.drop_column("client_mutation_id")
