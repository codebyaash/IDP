"""initial schema

Revision ID: 20260602_0001
Revises:
Create Date: 2026-06-02 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "20260602_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "projects",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("cloud_provider", sa.String(length=40), nullable=False),
        sa.Column("environment", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("monthly_cost", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("environment IN ('dev', 'stage', 'prod')", name="ck_projects_environment"),
        sa.CheckConstraint("monthly_cost >= 0", name="ck_projects_monthly_cost_non_negative"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_projects_user_created_at", "projects", ["user_id", "created_at"])

    op.create_table(
        "deployments",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("environment", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("template_name", sa.String(length=255), nullable=False),
        sa.Column("plan_json", sa.JSON(), nullable=False),
        sa.Column("estimated_monthly_cost", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("environment IN ('dev', 'stage', 'prod')", name="ck_deployments_environment"),
        sa.CheckConstraint("estimated_monthly_cost >= 0", name="ck_deployments_cost_non_negative"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_deployments_project_environment_created_at",
        "deployments",
        ["project_id", "environment", "created_at"],
    )

    op.create_table(
        "iac_templates",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("environment", sa.String(length=40), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_type", sa.String(length=40), nullable=False),
        sa.Column("raw_content", sa.Text(), nullable=False),
        sa.Column("parsed_json", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("environment IN ('dev', 'stage', 'prod')", name="ck_iac_templates_environment"),
        sa.CheckConstraint("version > 0", name="ck_iac_templates_version_positive"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "environment", "version", name="uq_iac_templates_project_environment_version"),
    )
    op.create_index(
        "ix_iac_templates_project_environment_created_at",
        "iac_templates",
        ["project_id", "environment", "created_at"],
    )

    op.create_table(
        "resources",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("deployment_id", sa.String(), nullable=False),
        sa.Column("environment", sa.String(length=40), nullable=False),
        sa.Column("resource_name", sa.String(length=255), nullable=False),
        sa.Column("resource_type", sa.String(length=255), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("region", sa.String(length=80), nullable=False),
        sa.Column("dependencies", sa.JSON(), nullable=False),
        sa.Column("estimated_monthly_cost", sa.Float(), nullable=False),
        sa.Column("resource_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("environment IN ('dev', 'stage', 'prod')", name="ck_resources_environment"),
        sa.CheckConstraint("estimated_monthly_cost >= 0", name="ck_resources_cost_non_negative"),
        sa.ForeignKeyConstraint(["deployment_id"], ["deployments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("deployment_id", "resource_name", name="uq_resources_deployment_resource_name"),
    )
    op.create_index("ix_resources_deployment", "resources", ["deployment_id"])
    op.create_index("ix_resources_project_environment", "resources", ["project_id", "environment"])

    op.create_table(
        "rollback_events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("environment", sa.String(length=40), nullable=False),
        sa.Column("source_deployment_id", sa.String(), nullable=False),
        sa.Column("rollback_deployment_id", sa.String(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("environment IN ('dev', 'stage', 'prod')", name="ck_rollback_events_environment"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rollback_deployment_id"], ["deployments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_deployment_id"], ["deployments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_rollback_events_project_environment_created_at",
        "rollback_events",
        ["project_id", "environment", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_rollback_events_project_environment_created_at", table_name="rollback_events")
    op.drop_table("rollback_events")
    op.drop_index("ix_resources_project_environment", table_name="resources")
    op.drop_index("ix_resources_deployment", table_name="resources")
    op.drop_table("resources")
    op.drop_index("ix_iac_templates_project_environment_created_at", table_name="iac_templates")
    op.drop_table("iac_templates")
    op.drop_index("ix_deployments_project_environment_created_at", table_name="deployments")
    op.drop_table("deployments")
    op.drop_index("ix_projects_user_created_at", table_name="projects")
    op.drop_table("projects")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
