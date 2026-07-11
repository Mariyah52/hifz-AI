"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-08

Creates every table as of Phase 17 in one migration, since this project
had no migrations at all through Phases 10-16 (schema was managed by
`Base.metadata.create_all`). Going forward, new tables/columns get their
own incremental migration instead of being folded in here.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "teacher_profiles",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False, unique=True),
    )

    op.create_table(
        "parent_profiles",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False, unique=True),
    )

    op.create_table(
        "classes",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("teacher_id", sa.String(), sa.ForeignKey("teacher_profiles.id"), nullable=True),
    )

    op.create_table(
        "student_profiles",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("class_id", sa.String(), sa.ForeignKey("classes.id"), nullable=True),
        sa.Column("current_streak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("longest_streak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_active_date", sa.Date(), nullable=True),
        sa.Column("freezes_available", sa.Integer(), nullable=False, server_default="2"),
    )

    op.create_table(
        "parent_child_links",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("parent_id", sa.String(), sa.ForeignKey("parent_profiles.id"), nullable=False),
        sa.Column("student_id", sa.String(), sa.ForeignKey("student_profiles.id"), nullable=False),
    )

    op.create_table(
        "sabaqs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("student_id", sa.String(), sa.ForeignKey("student_profiles.id"), nullable=False),
        sa.Column("surah_number", sa.Integer(), nullable=False),
        sa.Column("surah_name", sa.String(), nullable=False),
        sa.Column("from_ayah", sa.Integer(), nullable=False),
        sa.Column("to_ayah", sa.Integer(), nullable=False),
        sa.Column("assigned_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="not_started"),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_sabaqs_student_id", "sabaqs", ["student_id"])

    op.create_table(
        "practice_attempts",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("student_id", sa.String(), sa.ForeignKey("student_profiles.id"), nullable=False),
        sa.Column("surah_number", sa.Integer(), nullable=False),
        sa.Column("surah_name", sa.String(), nullable=False),
        sa.Column("from_ayah", sa.Integer(), nullable=False),
        sa.Column("to_ayah", sa.Integer(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="recorded"),
        sa.Column("expected_min_seconds", sa.Float(), nullable=False),
        sa.Column("expected_max_seconds", sa.Float(), nullable=False),
        sa.Column("within_expected_range", sa.Boolean(), nullable=False),
        sa.Column("audio_url", sa.String(), nullable=True),
    )
    op.create_index("ix_practice_attempts_student_id", "practice_attempts", ["student_id"])

    op.create_table(
        "test_sessions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("student_id", sa.String(), sa.ForeignKey("student_profiles.id"), nullable=False),
        sa.Column("surah_number", sa.Integer(), nullable=False),
        sa.Column("surah_name", sa.String(), nullable=False),
        sa.Column("from_ayah", sa.Integer(), nullable=False),
        sa.Column("to_ayah", sa.Integer(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("score_percent", sa.Integer(), nullable=False),
    )
    op.create_index("ix_test_sessions_student_id", "test_sessions", ["student_id"])

    op.create_table(
        "test_results",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("session_id", sa.String(), sa.ForeignKey("test_sessions.id"), nullable=False),
        sa.Column("ayah_number", sa.Integer(), nullable=False),
        sa.Column("self_mark", sa.String(), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=False),
    )
    op.create_index("ix_test_results_session_id", "test_results", ["session_id"])

    op.create_table(
        "teacher_feedback",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("student_id", sa.String(), sa.ForeignKey("student_profiles.id"), nullable=False),
        sa.Column("teacher_id", sa.String(), sa.ForeignKey("teacher_profiles.id"), nullable=True),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_teacher_feedback_student_id", "teacher_feedback", ["student_id"])

    op.create_table(
        "review_schedules",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("sabaq_id", sa.String(), sa.ForeignKey("sabaqs.id"), nullable=False, unique=True),
        sa.Column("student_id", sa.String(), sa.ForeignKey("student_profiles.id"), nullable=False),
        sa.Column("repetition_number", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ease_factor", sa.Float(), nullable=False, server_default="2.5"),
        sa.Column("interval_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("last_reviewed_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_review_schedules_sabaq_id", "review_schedules", ["sabaq_id"])
    op.create_index("ix_review_schedules_student_id", "review_schedules", ["student_id"])

    op.create_table(
        "practice_attempt_analyses",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("attempt_id", sa.String(), sa.ForeignKey("practice_attempts.id"), nullable=False, unique=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("transcribed_text", sa.Text(), nullable=True),
        sa.Column("reference_word_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("matched_word_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_practice_attempt_analyses_attempt_id", "practice_attempt_analyses", ["attempt_id"])

    op.create_table(
        "practice_mistakes",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "analysis_id", sa.String(), sa.ForeignKey("practice_attempt_analyses.id"), nullable=False
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("mistake_type", sa.String(), nullable=False),
        sa.Column("ayah_number", sa.Integer(), nullable=True),
        sa.Column("reference_word", sa.String(), nullable=True),
        sa.Column("transcribed_word", sa.String(), nullable=True),
    )
    op.create_index("ix_practice_mistakes_analysis_id", "practice_mistakes", ["analysis_id"])

    op.create_table(
        "achievements",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("student_id", sa.String(), sa.ForeignKey("student_profiles.id"), nullable=False),
        sa.Column("achievement_key", sa.String(), nullable=False),
        sa.Column("earned_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_achievements_student_id", "achievements", ["student_id"])
    op.create_index("ix_achievements_achievement_key", "achievements", ["achievement_key"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("notification_type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("related_id", sa.String(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])

    op.create_table(
        "push_subscriptions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("endpoint", sa.Text(), nullable=False),
        sa.Column("p256dh_key", sa.String(), nullable=False),
        sa.Column("auth_key", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_push_subscriptions_user_id", "push_subscriptions", ["user_id"])
    op.create_index("ix_push_subscriptions_endpoint", "push_subscriptions", ["endpoint"], unique=True)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_password_reset_tokens_user_id", "password_reset_tokens", ["user_id"])
    op.create_index(
        "ix_password_reset_tokens_token_hash", "password_reset_tokens", ["token_hash"], unique=True
    )

    op.create_table(
        "audit_log_entries",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_log_entries_user_id", "audit_log_entries", ["user_id"])
    op.create_index("ix_audit_log_entries_action", "audit_log_entries", ["action"])
    op.create_index("ix_audit_log_entries_created_at", "audit_log_entries", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_log_entries")
    op.drop_table("password_reset_tokens")
    op.drop_table("refresh_tokens")
    op.drop_table("push_subscriptions")
    op.drop_table("notifications")
    op.drop_table("achievements")
    op.drop_table("practice_mistakes")
    op.drop_table("practice_attempt_analyses")
    op.drop_table("review_schedules")
    op.drop_table("teacher_feedback")
    op.drop_table("test_results")
    op.drop_table("test_sessions")
    op.drop_table("practice_attempts")
    op.drop_table("sabaqs")
    op.drop_table("parent_child_links")
    op.drop_table("student_profiles")
    op.drop_table("classes")
    op.drop_table("parent_profiles")
    op.drop_table("teacher_profiles")
    op.drop_table("users")
