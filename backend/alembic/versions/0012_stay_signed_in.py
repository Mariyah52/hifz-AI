"""Stay signed in — track long-lived vs. session-only refresh tokens

Revision ID: 0012_stay_signed_in
Revises: 0011_ai_test_analysis
Create Date: 2026-07-11

Adds `refresh_tokens.long_lived`. Login now offers a "Stay signed in"
checkbox: checked issues a refresh token with the existing default expiry
(`refresh_token_expire_days`, 30 days) and the frontend keeps it in
localStorage (survives closing the browser); unchecked issues one with a
short expiry (`short_refresh_token_expire_days`) and the frontend keeps it
in sessionStorage instead (cleared the moment the tab/browser closes) —
the short backend expiry is defense-in-depth in case that token is ever
extracted some other way. `long_lived` is carried forward every time a
token is rotated on `/auth/refresh`, so the choice made at login persists
for the life of that session. Defaults to True for the migration itself so
every refresh token issued before this feature existed keeps behaving
exactly as it did (nobody already logged in gets silently logged out).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0012_stay_signed_in"
down_revision: Union[str, None] = "0011_ai_test_analysis"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("refresh_tokens") as batch_op:
        batch_op.add_column(
            sa.Column("long_lived", sa.Boolean(), nullable=False, server_default=sa.true())
        )


def downgrade() -> None:
    with op.batch_alter_table("refresh_tokens") as batch_op:
        batch_op.drop_column("long_lived")
