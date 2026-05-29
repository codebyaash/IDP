from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Optional

import hcl2
import yaml

from app.schemas.deployment import (
    Deployment,
    DeploymentPlan,
    DeploymentStep,
    ParsedTemplate,
    PlanChange,
    Resource,
    TemplateValidation,
)

COST_BY_TYPE = {
    "azurerm_linux_virtual_machine": 42,
    "azurerm_windows_virtual_machine": 68,
    "azurerm_storage_account": 12,
    "azurerm_virtual_network": 5,
    "azurerm_subnet": 2,
    "azurerm_public_ip": 4,
    "azurerm_network_security_group": 3,
    "resource_group": 0,
    "storage_account": 12,
    "virtual_network": 5,
    "subnet": 2,
    "vm": 42,
}


def list_projects() -> list[dict[str, Any]]:
    return [
        {
            "id": "demo-azure-core",
            "name": "Azure Core Network",
            "cloud_provider": "azure",
            "environment": "dev",
            "status": "healthy",
            "monthly_cost": 63,
        }
    ]


def parse_template_content(file_name: str, content: str) -> ParsedTemplate:
    extension = Path(file_name).suffix.lower()

    if extension == ".tf":
        document = hcl2.loads(content)
        resources = _resources_from_terraform(document)
    elif extension in {".yaml", ".yml"}:
        document = yaml.safe_load(content) or {}
        resources = _resources_from_mapping(document)
    elif extension == ".json":
        document = json.loads(content)
        resources = _resources_from_mapping(document)
    elif extension == ".bicep":
        resources = _resources_from_bicep(content)
    else:
        raise ValueError(f"Unsupported template type: {extension or 'unknown'}")

    return ParsedTemplate(file_name=file_name, file_type=extension.replace(".", ""), resources=resources)


def validate_template(file_name: str, content: str) -> TemplateValidation:
    try:
        parsed = parse_template_content(file_name, content)
    except Exception as exc:
        return TemplateValidation(file_name=file_name, valid=False, errors=[str(exc)])

    warnings = []
    if not parsed.resources:
        warnings.append("No deployable resources were detected.")

    return TemplateValidation(
        file_name=file_name,
        valid=True,
        warnings=warnings,
        resources_found=len(parsed.resources),
    )


def generate_plan(template: ParsedTemplate) -> DeploymentPlan:
    changes = [
        PlanChange(action="create", resource=resource, reason="Resource is not present in the simulated state.")
        for resource in template.resources
    ]
    total_cost = sum(change.resource.estimated_monthly_cost for change in changes)
    return DeploymentPlan(
        template_name=template.file_name,
        summary={"create": len(changes), "update": 0, "delete": 0},
        changes=changes,
        estimated_monthly_cost=total_cost,
    )


def create_deployment(plan: DeploymentPlan) -> Deployment:
    steps = [
        DeploymentStep(name="Queued", status="success", logs=["Deployment request accepted."], sequence_order=1),
        DeploymentStep(name="Validate", status="success", logs=["IaC syntax and required fields passed."], sequence_order=2),
        DeploymentStep(name="Plan", status="success", logs=[f"{plan.summary['create']} create actions generated."], sequence_order=3),
        DeploymentStep(name="Deploy", status="success", logs=["Simulated Azure deployment completed."], sequence_order=4),
        DeploymentStep(name="Record History", status="success", logs=["Deployment version stored for rollback."], sequence_order=5),
    ]
    return Deployment(
        id=str(uuid.uuid4()),
        project_id="demo-azure-core",
        status="success",
        plan=plan,
        steps=steps,
    )


def list_sample_deployments(project_id: str) -> list[Deployment]:
    resource = _build_resource("core-vnet", "azurerm_virtual_network", region="eastus")
    plan = DeploymentPlan(
        template_name="azure-network.tf",
        summary={"create": 1, "update": 0, "delete": 0},
        changes=[PlanChange(action="create", resource=resource, reason="Initial baseline deployment.")],
        estimated_monthly_cost=resource.estimated_monthly_cost,
    )
    deployment = create_deployment(plan)
    deployment.project_id = project_id
    return [deployment]


def _resources_from_terraform(document: dict[str, Any]) -> list[Resource]:
    resources = []
    for block in document.get("resource", []):
        for resource_type, named_resources in block.items():
            for name, config in named_resources.items():
                resources.append(
                    _build_resource(
                        name=name,
                        resource_type=resource_type,
                        region=config.get("location", "eastus") if isinstance(config, dict) else "eastus",
                    )
                )
    return resources


def _resources_from_mapping(document: dict[str, Any]) -> list[Resource]:
    raw_resources = document.get("resources", [])
    resources = []
    for item in raw_resources:
        resources.append(
            _build_resource(
                name=item.get("name", "unnamed-resource"),
                resource_type=item.get("type", "resource"),
                region=item.get("region", item.get("location", "eastus")),
                dependencies=item.get("depends_on", item.get("dependencies", [])),
            )
        )
    return resources


def _resources_from_bicep(content: str) -> list[Resource]:
    resources = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped.startswith("resource "):
            continue
        parts = stripped.split()
        if len(parts) >= 4:
            name = parts[1]
            resource_type = parts[3].strip("'").split("@")[0].replace("Microsoft.", "azure_").lower()
            resources.append(_build_resource(name=name, resource_type=resource_type))
    return resources


def _build_resource(
    name: str,
    resource_type: str,
    region: str = "eastus",
    dependencies: Optional[list[str]] = None,
) -> Resource:
    return Resource(
        name=name,
        type=resource_type,
        region=region,
        dependencies=dependencies or [],
        estimated_monthly_cost=COST_BY_TYPE.get(resource_type, 8),
    )
