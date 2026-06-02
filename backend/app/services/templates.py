from sqlalchemy import func, select
from sqlalchemy.orm import Session
from typing import Optional

from app.models import IacTemplate
from app.schemas.deployment import DeploymentPlan, ParsedTemplate
from app.services.resources import get_latest_project_resource_snapshot
from app.services.simulator import generate_plan, parse_template_content


def create_template(
    db: Session,
    project_id: str,
    raw_content: str,
    parsed: ParsedTemplate,
    environment: str = "dev",
) -> IacTemplate:
    version = _next_template_version(db, project_id, environment)
    template = IacTemplate(
        project_id=project_id,
        environment=environment,
        file_name=parsed.file_name,
        file_type=parsed.file_type,
        raw_content=raw_content,
        parsed_json=parsed.model_dump(),
        version=version,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def get_template(db: Session, template_id: str) -> Optional[IacTemplate]:
    return db.get(IacTemplate, template_id)


def list_templates(db: Session, project_id: str, environment: str = "dev") -> list[IacTemplate]:
    statement = (
        select(IacTemplate)
        .where(IacTemplate.project_id == project_id, IacTemplate.environment == environment)
        .order_by(IacTemplate.version.desc())
    )
    return list(db.scalars(statement))


def get_template_plan(db: Session, template_id: str) -> Optional[DeploymentPlan]:
    template = get_template(db, template_id)
    if template is None:
        return None
    parsed = parse_template_content(template.file_name, template.raw_content)
    current_resources = get_latest_project_resource_snapshot(db, template.project_id, template.environment)
    return generate_plan(parsed, current_resources=current_resources, environment=template.environment)


def _next_template_version(db: Session, project_id: str, environment: str = "dev") -> int:
    statement = select(func.max(IacTemplate.version)).where(
        IacTemplate.project_id == project_id,
        IacTemplate.environment == environment,
    )
    current = db.scalar(statement)
    return (current or 0) + 1
