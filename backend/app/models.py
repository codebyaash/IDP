from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def new_id() -> str:
    return str(uuid4())


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        CheckConstraint("environment IN ('dev', 'stage', 'prod')", name="ck_projects_environment"),
        CheckConstraint("monthly_cost >= 0", name="ck_projects_monthly_cost_non_negative"),
        Index("ix_projects_user_created_at", "user_id", "created_at"),
        Index("ix_projects_organization_created_at", "organization_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False, default="deployforge.local")
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    cloud_provider: Mapped[str] = mapped_column(String(40), nullable=False, default="azure")
    environment: Mapped[str] = mapped_column(String(40), nullable=False, default="dev")
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="healthy")
    monthly_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="projects")
    templates: Mapped[list["IacTemplate"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    deployments: Mapped[list["DeploymentRecord"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    resources: Mapped[list["ResourceRecord"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    rollback_events: Mapped[list["RollbackEvent"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class IacTemplate(Base):
    __tablename__ = "iac_templates"
    __table_args__ = (
        CheckConstraint("environment IN ('dev', 'stage', 'prod')", name="ck_iac_templates_environment"),
        CheckConstraint("version > 0", name="ck_iac_templates_version_positive"),
        UniqueConstraint("project_id", "environment", "version", name="uq_iac_templates_project_environment_version"),
        Index("ix_iac_templates_project_environment_created_at", "project_id", "environment", "created_at"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    environment: Mapped[str] = mapped_column(String(40), nullable=False, default="dev")
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(40), nullable=False)
    raw_content: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    project: Mapped[Project] = relationship(back_populates="templates")


class DeploymentRecord(Base):
    __tablename__ = "deployments"
    __table_args__ = (
        CheckConstraint("environment IN ('dev', 'stage', 'prod')", name="ck_deployments_environment"),
        CheckConstraint("estimated_monthly_cost >= 0", name="ck_deployments_cost_non_negative"),
        Index("ix_deployments_project_environment_created_at", "project_id", "environment", "created_at"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    environment: Mapped[str] = mapped_column(String(40), nullable=False, default="dev")
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    template_name: Mapped[str] = mapped_column(String(255), nullable=False)
    plan_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    estimated_monthly_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    project: Mapped[Project] = relationship(back_populates="deployments")
    resources: Mapped[list["ResourceRecord"]] = relationship(back_populates="deployment", cascade="all, delete-orphan")


class ResourceRecord(Base):
    __tablename__ = "resources"
    __table_args__ = (
        CheckConstraint("environment IN ('dev', 'stage', 'prod')", name="ck_resources_environment"),
        CheckConstraint("estimated_monthly_cost >= 0", name="ck_resources_cost_non_negative"),
        UniqueConstraint("deployment_id", "resource_name", name="uq_resources_deployment_resource_name"),
        Index("ix_resources_project_environment", "project_id", "environment"),
        Index("ix_resources_deployment", "deployment_id"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    deployment_id: Mapped[str] = mapped_column(ForeignKey("deployments.id", ondelete="CASCADE"), nullable=False)
    environment: Mapped[str] = mapped_column(String(40), nullable=False, default="dev")
    resource_name: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(80), nullable=False, default="azure")
    region: Mapped[str] = mapped_column(String(80), nullable=False, default="eastus")
    dependencies: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    estimated_monthly_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    resource_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    project: Mapped[Project] = relationship(back_populates="resources")
    deployment: Mapped[DeploymentRecord] = relationship(back_populates="resources")


class RollbackEvent(Base):
    __tablename__ = "rollback_events"
    __table_args__ = (
        CheckConstraint("environment IN ('dev', 'stage', 'prod')", name="ck_rollback_events_environment"),
        Index("ix_rollback_events_project_environment_created_at", "project_id", "environment", "created_at"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    environment: Mapped[str] = mapped_column(String(40), nullable=False, default="dev")
    source_deployment_id: Mapped[str] = mapped_column(ForeignKey("deployments.id", ondelete="CASCADE"), nullable=False)
    rollback_deployment_id: Mapped[str] = mapped_column(ForeignKey("deployments.id", ondelete="CASCADE"), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False, default="Manual rollback")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    project: Mapped[Project] = relationship(back_populates="rollback_events")


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    organization_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    projects: Mapped[list[Project]] = relationship(back_populates="user", cascade="all, delete-orphan")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_user_created_at", "user_id", "created_at"),
        Index("ix_audit_logs_organization_created_at", "organization_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    project_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    environment: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="audit_logs")
