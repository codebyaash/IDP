from collections import defaultdict
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DeploymentRecord, ResourceRecord
from app.schemas.deployment import DeploymentPlan, Resource
from app.schemas.resource import CostBreakdownItem, CostEstimate, PersistedResource


def persist_resources_for_deployment(db: Session, deployment: DeploymentRecord, plan: DeploymentPlan) -> None:
    for change in plan.changes:
        resource = change.resource
        db.add(
            ResourceRecord(
                project_id=deployment.project_id,
                deployment_id=deployment.id,
                resource_name=resource.name,
                resource_type=resource.type,
                provider=resource.provider,
                region=resource.region,
                dependencies=resource.dependencies,
                estimated_monthly_cost=resource.estimated_monthly_cost,
                resource_metadata=resource.metadata,
            )
        )


def persist_resource_snapshot(
    db: Session,
    deployment: DeploymentRecord,
    resources: list[Resource],
) -> None:
    for resource in resources:
        db.add(
            ResourceRecord(
                project_id=deployment.project_id,
                deployment_id=deployment.id,
                resource_name=resource.name,
                resource_type=resource.type,
                provider=resource.provider,
                region=resource.region,
                dependencies=resource.dependencies,
                estimated_monthly_cost=resource.estimated_monthly_cost,
                resource_metadata=resource.metadata,
            )
        )


def get_deployment_resource_snapshot(db: Session, deployment_id: str) -> list[Resource]:
    statement = (
        select(ResourceRecord)
        .where(ResourceRecord.deployment_id == deployment_id)
        .order_by(ResourceRecord.resource_type.asc(), ResourceRecord.resource_name.asc())
    )
    return [
        Resource(
            name=resource.resource_name,
            type=resource.resource_type,
            provider=resource.provider,
            region=resource.region,
            dependencies=resource.dependencies,
            estimated_monthly_cost=resource.estimated_monthly_cost,
            metadata=resource.resource_metadata,
        )
        for resource in db.scalars(statement)
    ]


def get_latest_project_resource_snapshot(db: Session, project_id: str) -> list[Resource]:
    deployment = _latest_deployment(db, project_id)
    if deployment is None:
        return []
    return get_deployment_resource_snapshot(db, deployment.id)


def list_project_resources(db: Session, project_id: str) -> list[PersistedResource]:
    deployment = _latest_deployment(db, project_id)
    if deployment is None:
        return []

    statement = (
        select(ResourceRecord)
        .where(ResourceRecord.deployment_id == deployment.id)
        .order_by(ResourceRecord.resource_type.asc(), ResourceRecord.resource_name.asc())
    )
    return [PersistedResource.model_validate(resource, from_attributes=True) for resource in db.scalars(statement)]


def get_project_cost_estimate(db: Session, project_id: str) -> CostEstimate:
    resources = list_project_resources(db, project_id)
    breakdown: dict[str, list[float]] = defaultdict(list)

    for resource in resources:
        breakdown[resource.resource_type].append(resource.estimated_monthly_cost)

    items = [
        CostBreakdownItem(
            label=label,
            monthly_cost=sum(costs),
            resource_count=len(costs),
        )
        for label, costs in sorted(breakdown.items())
    ]
    total_monthly_cost = sum(item.monthly_cost for item in items)

    return CostEstimate(
        project_id=project_id,
        total_monthly_cost=total_monthly_cost,
        resource_count=len(resources),
        breakdown=items,
    )


def _latest_deployment(db: Session, project_id: str) -> Optional[DeploymentRecord]:
    statement = (
        select(DeploymentRecord)
        .where(DeploymentRecord.project_id == project_id)
        .order_by(DeploymentRecord.created_at.desc())
        .limit(1)
    )
    return db.scalar(statement)
