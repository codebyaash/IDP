from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Optional

from app.models import DeploymentRecord, Project, RollbackEvent
from app.schemas.deployment import Deployment, DeploymentPlan, DeploymentStep, PlanChange, Resource
from app.schemas.rollback import RollbackResult
from app.services.resources import get_deployment_resource_snapshot, persist_resource_snapshot
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
    persist_resource_snapshot(db, record, deployment.plan.target_resources)

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


def rollback_deployment(db: Session, deployment_id: str, reason: str = "Manual rollback") -> Optional[RollbackResult]:
    source = db.get(DeploymentRecord, deployment_id)
    if source is None or source.status != "success":
        return None

    resources = get_deployment_resource_snapshot(db, source.id)
    if not resources:
        resources = _resources_from_record_plan(source)

    plan = _rollback_plan(source.template_name, resources)
    steps = _rollback_steps(source.id, len(resources))
    record = DeploymentRecord(
        project_id=source.project_id,
        status="success",
        template_name=f"Rollback to {source.template_name}",
        plan_json={
            "rollback_from_deployment_id": source.id,
            "plan": plan.model_dump(),
            "steps": [step.model_dump() for step in steps],
        },
        estimated_monthly_cost=plan.estimated_monthly_cost,
    )
    db.add(record)
    db.flush()

    persist_resource_snapshot(db, record, resources)

    project = db.get(Project, source.project_id)
    if project is not None:
        project.monthly_cost = plan.estimated_monthly_cost
        project.status = "rolled_back"

    db.add(
        RollbackEvent(
            project_id=source.project_id,
            source_deployment_id=source.id,
            rollback_deployment_id=record.id,
            reason=reason,
        )
    )
    db.commit()
    db.refresh(record)

    return RollbackResult(
        source_deployment_id=source.id,
        rollback_deployment=_deployment_from_record(record),
    )


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


def _resources_from_record_plan(record: DeploymentRecord) -> list[Resource]:
    payload = record.plan_json or {}
    plan_payload = payload.get("plan", {})
    if not plan_payload:
        return []
    plan = DeploymentPlan.model_validate(plan_payload)
    return [change.resource for change in plan.changes]


def _rollback_plan(template_name: str, resources: list[Resource]) -> DeploymentPlan:
    changes = [
        PlanChange(
            action="rollback",
            resource=resource,
            reason="Restore resource from selected deployment snapshot.",
        )
        for resource in resources
    ]
    return DeploymentPlan(
        template_name=f"Rollback to {template_name}",
        summary={"create": 0, "update": len(resources), "delete": 0, "rollback": len(resources)},
        changes=changes,
        estimated_monthly_cost=sum(resource.estimated_monthly_cost for resource in resources),
        target_resources=resources,
    )


def _rollback_steps(source_deployment_id: str, resource_count: int) -> list[DeploymentStep]:
    return [
        DeploymentStep(
            name="Queued",
            status="success",
            logs=[f"Rollback requested for deployment {source_deployment_id}."],
            sequence_order=1,
        ),
        DeploymentStep(
            name="Snapshot",
            status="success",
            logs=[f"{resource_count} resources loaded from rollback target."],
            sequence_order=2,
        ),
        DeploymentStep(
            name="Plan",
            status="success",
            logs=["Rollback plan generated from stored deployment state."],
            sequence_order=3,
        ),
        DeploymentStep(
            name="Restore",
            status="success",
            logs=["Simulated resource state restored."],
            sequence_order=4,
        ),
        DeploymentStep(
            name="Record History",
            status="success",
            logs=["Rollback deployment version stored."],
            sequence_order=5,
        ),
    ]
