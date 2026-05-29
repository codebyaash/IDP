from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def new_id() -> str:
    return str(uuid4())


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    cloud_provider: Mapped[str] = mapped_column(String(40), nullable=False, default="azure")
    environment: Mapped[str] = mapped_column(String(40), nullable=False, default="dev")
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="healthy")
    monthly_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    templates: Mapped[list["IacTemplate"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    deployments: Mapped[list["DeploymentRecord"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class IacTemplate(Base):
    __tablename__ = "iac_templates"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(40), nullable=False)
    raw_content: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    project: Mapped[Project] = relationship(back_populates="templates")


class DeploymentRecord(Base):
    __tablename__ = "deployments"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    template_name: Mapped[str] = mapped_column(String(255), nullable=False)
    plan_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    estimated_monthly_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    project: Mapped[Project] = relationship(back_populates="deployments")
