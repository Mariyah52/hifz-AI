"""add last_quality to review_schedules

Revision ID: 0003_review_last_quality
Revises: 0002_multi_tenancy
Create Date: 2026-07-08

Phase 21's retention-rate metric needs to know each ReviewSchedule's most
recent SM-2 grading quality, which wasn't previously stored.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_review_last_quality"
down_revision: Union[str, None] = "0002_multi_tenancy"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("review_schedules") as batch_op:
        batch_op.add_column(sa.Column("last_quality", sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("review_schedules") as batch_op:
        batch_op.drop_column("last_quality")
