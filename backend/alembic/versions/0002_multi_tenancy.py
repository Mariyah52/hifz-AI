"""multi-tenancy: organizations

Revision ID: 0002_multi_tenancy
Revises: 0001_initial_schema
Create Date: 2026-07-08

Adds the `organizations` table and `organization_id` to `users` and
`classes` — the tenant boundary for Phase 18. Column is added nullable
first, backfilled with a default organization for any pre-existing rows
(so this migration is safe to run against a database that already has
real users in it, not just a fresh one), then tightened to NOT NULL.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_multi_tenancy"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_ORG_ID = "org_default000"


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("plan", sa.String(), nullable=False, server_default="free"),
        sa.Column("max_students", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("max_teachers", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("primary_color", sa.String(), nullable=True),
        sa.Column("logo_url", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=True)

    # A default org so any pre-existing users/classes (e.g. a database
    # that already ran Phase 10-17's migration before Phase 18 existed)
    # have somewhere to land, rather than the backfill below having
    # nothing to point at.
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "INSERT INTO organizations (id, name, slug, plan, max_students, max_teachers, created_at) "
            "VALUES (:id, :name, :slug, 'free', 30, 5, CURRENT_TIMESTAMP)"
        ),
        {"id": DEFAULT_ORG_ID, "name": "Default Organization", "slug": "default"},
    )

    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("organization_id", sa.String(), nullable=True))
    op.execute(sa.text("UPDATE users SET organization_id = :org_id").bindparams(org_id=DEFAULT_ORG_ID))
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("organization_id", nullable=False)
        batch_op.create_index("ix_users_organization_id", ["organization_id"])
        batch_op.create_foreign_key(
            "fk_users_organization_id", "organizations", ["organization_id"], ["id"]
        )

    with op.batch_alter_table("classes") as batch_op:
        batch_op.add_column(sa.Column("organization_id", sa.String(), nullable=True))
    op.execute(sa.text("UPDATE classes SET organization_id = :org_id").bindparams(org_id=DEFAULT_ORG_ID))
    with op.batch_alter_table("classes") as batch_op:
        batch_op.alter_column("organization_id", nullable=False)
        batch_op.create_index("ix_classes_organization_id", ["organization_id"])
        batch_op.create_foreign_key(
            "fk_classes_organization_id", "organizations", ["organization_id"], ["id"]
        )


def downgrade() -> None:
    with op.batch_alter_table("classes") as batch_op:
        batch_op.drop_constraint("fk_classes_organization_id", type_="foreignkey")
        batch_op.drop_index("ix_classes_organization_id")
        batch_op.drop_column("organization_id")

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint("fk_users_organization_id", type_="foreignkey")
        batch_op.drop_index("ix_users_organization_id")
        batch_op.drop_column("organization_id")

    op.drop_index("ix_organizations_slug", table_name="organizations")
    op.drop_table("organizations")
