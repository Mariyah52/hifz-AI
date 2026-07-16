"""add secondary_color welcome_message principal_message to organizations

Revision ID: 6d9e587bc8b3
Revises: 0015_billing
Create Date: 2026-07-16 22:52:54.926470

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6d9e587bc8b3"
down_revision: Union[str, None] = "0015_billing"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("organizations", sa.Column("secondary_color", sa.String(), nullable=True))
    op.add_column("organizations", sa.Column("welcome_message", sa.String(), nullable=True))
    op.add_column("organizations", sa.Column("principal_message", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("organizations", "principal_message")
    op.drop_column("organizations", "welcome_message")
    op.drop_column("organizations", "secondary_color")
