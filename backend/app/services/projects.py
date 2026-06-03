from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Optional

from app.core.security import hash_password
from app.models import Project, User
from app.schemas.project import ProjectCreate
from app.services.auth import organization_from_email


DEMO_USER_ID = "demo-user"
DEMO_USER_EMAIL = "demo@deployforge.local"
DEMO_USER_PASSWORD = "deployforge123"


def create_project(db: Session, payload: ProjectCreate, user: User) -> Project:
    project = Project(
        user_id=user.id,
        organization_id=user.organization_id,
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


def get_project(db: Session, project_id: str, organization_id: str) -> Optional[Project]:
    return db.scalar(select(Project).where(Project.id == project_id, Project.organization_id == organization_id))


def list_projects(db: Session, organization_id: str) -> list[Project]:
    return list(
        db.scalars(select(Project).where(Project.organization_id == organization_id).order_by(Project.created_at.desc()))
    )


def seed_demo_user_and_project(db: Session) -> None:
    user = db.get(User, DEMO_USER_ID)
    if user is None:
        organization_id, organization_name = organization_from_email(DEMO_USER_EMAIL)
        user = User(
            id=DEMO_USER_ID,
            email=DEMO_USER_EMAIL,
            organization_id=organization_id,
            organization_name=organization_name,
            password_hash=hash_password(DEMO_USER_PASSWORD),
        )
        db.add(user)
        db.flush()
    elif not user.organization_id:
        user.organization_id, user.organization_name = organization_from_email(user.email)

    project = db.get(Project, "demo-azure-core")
    if project is None:
        db.add(
            Project(
                id="demo-azure-core",
                user_id=user.id,
                organization_id=user.organization_id,
                name="Azure Core Network",
                cloud_provider="azure",
                environment="dev",
                status="healthy",
                monthly_cost=63,
            )
        )
    elif project.user_id != user.id:
        project.user_id = user.id
        project.organization_id = user.organization_id
    elif project.organization_id != user.organization_id:
        project.organization_id = user.organization_id

    db.commit()
