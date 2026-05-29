from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Optional

from app.models import DeploymentRecord, Project
from app.schemas.deployment import Deployment, DeploymentPlan, DeploymentStep
from app.services.simulator import create_deployment
from app.services.templates import get_template, get_template_plan


def deploy_template(db: Session, template_id: str) -> Optional[Deployment]:
    template = get_template(db, template_id)
    if template is None:
        return None

    plan = get_template_plan(db, template_id)
    if plan is None:
        return None

    deployment = create_deployment(plan, project_id=template.project_id)
    record = DeploymentRecord(
        id=deployment.id,
        project_id=template.project_id,
        status=deployment.status,
        template_name=template.file_name,
        plan_json={
            "template_id": template.id,
            "template_version": template.version,
            "plan": deployment.plan.model_dump(),
            "steps": [step.model_dump() for step in deployment.steps],
        },
        estimated_monthly_cost=deployment.plan.estimated_monthly_cost,
    )
    db.add(record)

    project = db.get(Project, template.project_id)
    if project is not None:
        project.monthly_cost = deployment.plan.estimated_monthly_cost
        project.status = "deployed"

    db.commit()
    db.refresh(record)
    return _deployment_from_record(record)


def list_deployments(db: Session, project_id: str) -> list[Deployment]:
    statement = (
        select(DeploymentRecord)
        .where(DeploymentRecord.project_id == project_id)
        .order_by(DeploymentRecord.created_at.desc())
    )
    return [_deployment_from_record(record) for record in db.scalars(statement)]


def get_deployment(db: Session, deployment_id: str) -> Optional[Deployment]:
    record = db.get(DeploymentRecord, deployment_id)
    if record is None:
        return None
    return _deployment_from_record(record)


def _deployment_from_record(record: DeploymentRecord) -> Deployment:
    payload = record.plan_json or {}
    plan = DeploymentPlan.model_validate(payload.get("plan", {}))
    steps = [DeploymentStep.model_validate(step) for step in payload.get("steps", [])]
    return Deployment(
        id=record.id,
        project_id=record.project_id,
        status=record.status,
        plan=plan,
        steps=steps,
        created_at=record.created_at,
    )
