"""organization profile audit

Revision ID: 20260603_0002
Revises: 20260602_0001
Create Date: 2026-06-03 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "20260603_0002"
down_revision = "20260602_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("organization_id", sa.String(length=255), nullable=False, server_default="deployforge.local"))
    op.add_column("users", sa.Column("organization_name", sa.String(length=255), nullable=False, server_default="Deployforge"))
    op.create_index("ix_users_organization_id", "users", ["organization_id"])

    op.add_column("projects", sa.Column("organization_id", sa.String(length=255), nullable=False, server_default="deployforge.local"))
    op.create_index("ix_projects_organization_created_at", "projects", ["organization_id", "created_at"])
    op.execute(
        "UPDATE projects SET organization_id = "
        "COALESCE((SELECT users.organization_id FROM users WHERE users.id = projects.user_id), organization_id)"
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("organization_id", sa.String(length=255), nullable=False),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.String(length=255), nullable=True),
        sa.Column("project_id", sa.String(), nullable=True),
        sa.Column("environment", sa.String(length=40), nullable=True),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_user_created_at", "audit_logs", ["user_id", "created_at"])
    op.create_index("ix_audit_logs_organization_created_at", "audit_logs", ["organization_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_organization_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_created_at", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_projects_organization_created_at", table_name="projects")
    op.drop_column("projects", "organization_id")
    op.drop_index("ix_users_organization_id", table_name="users")
    op.drop_column("users", "organization_name")
    op.drop_column("users", "organization_id")
