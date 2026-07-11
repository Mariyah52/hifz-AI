"""communication tables

Revision ID: 0008_communication
Revises: 0007_certificates
Create Date: 2026-07-08

Phase 28: direct messaging (conversations + messages, with optional
voice-note/file attachments reusing Phase 10's media storage),
announcements, and homework.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0008_communication"
down_revision: Union[str, None] = "0007_certificates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_a_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("user_b_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_a_id", "user_b_id", name="uq_conversation_pair"),
    )
    op.create_index("ix_conversations_user_a_id", "conversations", ["user_a_id"])
    op.create_index("ix_conversations_user_b_id", "conversations", ["user_b_id"])

    op.create_table(
        "direct_messages",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("conversation_id", sa.String(), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("sender_user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("attachment_url", sa.String(), nullable=True),
        sa.Column("attachment_type", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_direct_messages_conversation_id", "direct_messages", ["conversation_id"])

    op.create_table(
        "announcements",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("organization_id", sa.String(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("class_id", sa.String(), sa.ForeignKey("classes.id"), nullable=True),
        sa.Column("author_user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_announcements_organization_id", "announcements", ["organization_id"])
    op.create_index("ix_announcements_class_id", "announcements", ["class_id"])

    op.create_table(
        "homework",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("class_id", sa.String(), sa.ForeignKey("classes.id"), nullable=False),
        sa.Column("created_by_teacher_id", sa.String(), sa.ForeignKey("teacher_profiles.id"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_homework_class_id", "homework", ["class_id"])


def downgrade() -> None:
    op.drop_table("homework")
    op.drop_table("announcements")
    op.drop_table("direct_messages")
    op.drop_table("conversations")
