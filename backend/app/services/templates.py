from sqlalchemy import func, select
from sqlalchemy.orm import Session
from typing import Optional

from app.models import IacTemplate
from app.schemas.deployment import DeploymentPlan, ParsedTemplate
from app.services.simulator import generate_plan, parse_template_content


def create_template(db: Session, project_id: str, raw_content: str, parsed: ParsedTemplate) -> IacTemplate:
    version = _next_template_version(db, project_id)
    template = IacTemplate(
        project_id=project_id,
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


def list_templates(db: Session, project_id: str) -> list[IacTemplate]:
    statement = select(IacTemplate).where(IacTemplate.project_id == project_id).order_by(IacTemplate.version.desc())
    return list(db.scalars(statement))


def get_template_plan(db: Session, template_id: str) -> Optional[DeploymentPlan]:
    template = get_template(db, template_id)
    if template is None:
        return None
    parsed = parse_template_content(template.file_name, template.raw_content)
    return generate_plan(parsed)


def _next_template_version(db: Session, project_id: str) -> int:
    statement = select(func.max(IacTemplate.version)).where(IacTemplate.project_id == project_id)
    current = db.scalar(statement)
    return (current or 0) + 1
