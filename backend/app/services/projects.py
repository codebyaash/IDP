from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Optional

from app.models import Project
from app.schemas.project import ProjectCreate


def create_project(db: Session, payload: ProjectCreate) -> Project:
    project = Project(
        name=payload.name,
        cloud_provider=payload.cloud_provider,
        environment=payload.environment,
        status="healthy",
        monthly_cost=0,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_project(db: Session, project_id: str) -> Optional[Project]:
    return db.get(Project, project_id)


def list_projects(db: Session) -> list[Project]:
    return list(db.scalars(select(Project).order_by(Project.created_at.desc())))


def seed_demo_project(db: Session) -> None:
    has_projects = db.scalar(select(Project.id).limit(1))
    if has_projects:
        return

    db.add(
        Project(
            id="demo-azure-core",
            name="Azure Core Network",
            cloud_provider="azure",
            environment="dev",
            status="healthy",
            monthly_cost=63,
        )
    )
    db.commit()
