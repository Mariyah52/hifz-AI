"""Data privacy — account deletion/anonymization tracking

Revision ID: 0013_data_privacy
Revises: 0012_stay_signed_in
Create Date: 2026-07-14

Adds `users.deleted_at` and `users.anonymized`. See
services/data_privacy.py's module docstring for the full explanation of
why account "deletion" in this app means anonymizing the User row in
place rather than hard-deleting it: other real rows (a conversation the
deleted user was part of, a certificate a teacher issued, a live class
they hosted) hold a non-nullable foreign key to `users.id`, and this
project has no ON DELETE CASCADE configured anywhere (a deliberate
choice elsewhere in the codebase — cascades are handled in application
code, not the schema). Hard-deleting the row would either orphan those
FKs (rejected by Postgres) or force cascading deletes into other real
users' own data, which is worse for privacy, not better.

`deleted_at` set means the account has gone through the deletion flow;
`anonymized` is redundant with `deleted_at is not None` today but kept
as an explicit, queryable boolean rather than relying on every caller to
remember "not null means anonymized" — cheap insurance against a future
migration adding an unrelated use for `deleted_at`.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0013_data_privacy"
down_revision: Union[str, None] = "0012_stay_signed_in"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(
            sa.Column("anonymized", sa.Boolean(), nullable=False, server_default=sa.false())
        )


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("anonymized")
        batch_op.drop_column("deleted_at")
