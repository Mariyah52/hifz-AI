"""Billing — Stripe customer/subscription tracking on organizations

Revision ID: 0015_billing
Revises: 0014_write_api_webhooks
Create Date: 2026-07-16

Adds `stripe_customer_id`, `stripe_subscription_id`, `subscription_status`
to `organizations`. All nullable — an org that never touches billing
(stays on the free plan forever) never gets these populated at all. See
services/billing.py for how they get set.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0015_billing"
down_revision: Union[str, None] = "0014_write_api_webhooks"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("organizations") as batch_op:
        batch_op.add_column(sa.Column("stripe_customer_id", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("stripe_subscription_id", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("subscription_status", sa.String(), nullable=True))
        batch_op.create_index("ix_organizations_stripe_customer_id", ["stripe_customer_id"])
        batch_op.create_index("ix_organizations_stripe_subscription_id", ["stripe_subscription_id"])


def downgrade() -> None:
    with op.batch_alter_table("organizations") as batch_op:
        batch_op.drop_index("ix_organizations_stripe_subscription_id")
        batch_op.drop_index("ix_organizations_stripe_customer_id")
        batch_op.drop_column("subscription_status")
        batch_op.drop_column("stripe_subscription_id")
        batch_op.drop_column("stripe_customer_id")
