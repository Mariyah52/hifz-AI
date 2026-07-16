"""Write API + Webhooks — API key scopes, webhook subscriptions, external attendance/grade records

Revision ID: 0014_write_api_webhooks
Revises: 0013_data_privacy
Create Date: 2026-07-15

Four things:

1. `api_keys.scopes` — a comma-separated scope string ('read' or
   'read,write'), same convention as `chat_messages.tools_called`
   elsewhere in this codebase. Defaults every existing key to `'read'`
   on migration, so no key that exists today silently gains write
   access it wasn't issued for — an org has to explicitly create (or
   an admin has to explicitly re-issue) a key with write scope.

2. `webhooks` — one row per URL an organization wants HifzAI to POST
   events to. `secret` is stored in plaintext (not hashed) because,
   unlike an API key, HifzAI is the one computing an HMAC signature
   with it on every outbound delivery — a one-way hash would make that
   impossible. This is the same tradeoff Stripe/GitHub-style outbound
   webhook secrets make.

3. `webhook_delivery_logs` — a short delivery history per webhook, for
   an admin to see "is this actually working" without needing real
   external log aggregation.

4. `external_attendance_records` / `external_grade_records` — the
   actual data an external LMS pushes in via the new write endpoints.
   Deliberately separate tables from this app's own internal attendance
   (`LiveSessionParticipant`) and grades (`TestSession.score_percent`)
   rather than writing into those directly — an external system's
   attendance/grading is a different source of truth with different
   provenance (which API key pushed it, when), and conflating the two
   would make it impossible to tell "the student did this in HifzAI"
   from "an external system says this happened."
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0014_write_api_webhooks"
down_revision: Union[str, None] = "0013_data_privacy"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("api_keys") as batch_op:
        batch_op.add_column(
            sa.Column("scopes", sa.String(), nullable=False, server_default="read")
        )

    op.create_table(
        "webhooks",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("organization_id", sa.String(), sa.ForeignKey("organizations.id"), index=True, nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("secret", sa.String(), nullable=False),
        sa.Column("event_types", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by_user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "webhook_delivery_logs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("webhook_id", sa.String(), sa.ForeignKey("webhooks.id"), index=True, nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("response_snippet", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, index=True),
    )

    op.create_table(
        "external_attendance_records",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("student_id", sa.String(), sa.ForeignKey("student_profiles.id"), index=True, nullable=False),
        sa.Column("api_key_id", sa.String(), sa.ForeignKey("api_keys.id"), nullable=False),
        sa.Column("session_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("source_label", sa.String(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "external_grade_records",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("student_id", sa.String(), sa.ForeignKey("student_profiles.id"), index=True, nullable=False),
        sa.Column("api_key_id", sa.String(), sa.ForeignKey("api_keys.id"), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("max_score", sa.Float(), nullable=False),
        sa.Column("recorded_date", sa.Date(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("external_grade_records")
    op.drop_table("external_attendance_records")
    op.drop_table("webhook_delivery_logs")
    op.drop_table("webhooks")
    with op.batch_alter_table("api_keys") as batch_op:
        batch_op.drop_column("scopes")
