"""marketplace tables

Revision ID: 0009_marketplace
Revises: 0008_communication
Create Date: 2026-07-09

Phase 29: marketplace catalog (question banks, revision plans, premium
reciters, themes, plugins) an institute can install, plus
per-organization install tracking. Catalog rows are seeded here, once —
there's no admin-facing "publish a new catalog item" flow; see
`app/models/marketplace.py`'s `MarketplaceItem` docstring for why.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0009_marketplace"
down_revision: Union[str, None] = "0008_communication"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


marketplace_items_table = sa.table(
    "marketplace_items",
    sa.column("id", sa.String),
    sa.column("category", sa.String),
    sa.column("name", sa.String),
    sa.column("description", sa.Text),
    sa.column("price_cents", sa.Integer),
    sa.column("is_premium", sa.Boolean),
    sa.column("config_json", sa.Text),
)


def upgrade() -> None:
    op.create_table(
        "marketplace_items",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_premium", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("config_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_marketplace_items_category", "marketplace_items", ["category"])

    op.create_table(
        "organization_marketplace_installs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("organization_id", sa.String(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("item_id", sa.String(), sa.ForeignKey("marketplace_items.id"), nullable=False),
        sa.Column("installed_by_user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("installed_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "item_id", name="uq_org_marketplace_item"),
    )
    op.create_index(
        "ix_organization_marketplace_installs_organization_id",
        "organization_marketplace_installs",
        ["organization_id"],
    )
    op.create_index(
        "ix_organization_marketplace_installs_item_id", "organization_marketplace_installs", ["item_id"]
    )

    op.bulk_insert(
        marketplace_items_table,
        [
            {
                "id": "mkt_juz_amma_bank", "category": "question_bank", "name": "Juz Amma Test Bank",
                "description": "Curated multiple-choice and recitation questions covering Juz 30, ready to assign.",
                "price_cents": 0, "is_premium": False, "config_json": None,
            },
            {
                "id": "mkt_trial_exam_pack", "category": "question_bank", "name": "Hifz Trial Exam Pack",
                "description": "A full mock-exam question bank spanning all 12 Phase 22 test modes.",
                "price_cents": 1900, "is_premium": True, "config_json": None,
            },
            {
                "id": "mkt_40day_plan", "category": "revision_plan", "name": "40-Day Juz Refresher",
                "description": "A structured 40-day revision cadence template covering one juz per rotation.",
                "price_cents": 0, "is_premium": False, "config_json": None,
            },
            {
                "id": "mkt_ramadan_cycle", "category": "revision_plan", "name": "Ramadan Full Qur'an Cycle",
                "description": "A 30-day full-Qur'an revision plan template timed to Ramadan.",
                "price_cents": 1500, "is_premium": True, "config_json": None,
            },
            {
                "id": "mkt_reciter_alafasy", "category": "reciter", "name": "Mishary Al-Afasy (Premium)",
                "description": "Adds Mishary Al-Afasy as an available reference reciter alongside Al-Husary.",
                "price_cents": 999, "is_premium": True,
                "config_json": '{"reciterEdition": "ar.alafasy"}',
            },
            {
                "id": "mkt_theme_emerald", "category": "theme", "name": "Emerald Manuscript",
                "description": "A cooler, emerald-accented variant of the default manuscript theme.",
                "price_cents": 0, "is_premium": False,
                "config_json": '{"primaryColor": "#0f766e"}',
            },
            {
                "id": "mkt_theme_maroon", "category": "theme", "name": "Maroon Binding",
                "description": "A warmer, maroon-leather-accented variant, usable as the primary brand color.",
                "price_cents": 499, "is_premium": True,
                "config_json": '{"primaryColor": "#7c2d3e"}',
            },
            {
                "id": "mkt_plugin_attendance_export", "category": "plugin", "name": "Attendance Export (CSV)",
                "description": "Adds a CSV export of live-class attendance records for institutional record-keeping.",
                "price_cents": 0, "is_premium": False, "config_json": None,
            },
            {
                "id": "mkt_plugin_parent_sms", "category": "plugin", "name": "Parent SMS Digest",
                "description": "An SMS-based weekly parent digest, alongside the existing email/push channels.",
                "price_cents": 1299, "is_premium": True, "config_json": None,
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("organization_marketplace_installs")
    op.drop_table("marketplace_items")
