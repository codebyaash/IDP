from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any, Optional

import hcl2
import yaml

from app.schemas.deployment import (
    Deployment,
    DeploymentPlan,
    DeploymentStep,
    DriftReport,
    ParsedTemplate,
    PlanChange,
    PolicyViolation,
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
    "azurerm_resource_group": 0,
    "resource_group": 0,
    "storage_account": 12,
    "virtual_network": 5,
    "subnet": 2,
    "vm": 42,
}

TERRAFORM_REFERENCE_PATTERN = re.compile(r"\${([A-Za-z0-9_]+)\.([A-Za-z0-9_]+)\.[^}]+}")


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


def generate_plan(template: ParsedTemplate, current_resources: Optional[list[Resource]] = None) -> DeploymentPlan:
    current_by_name = {resource.name: resource for resource in current_resources or []}
    desired_by_name = {resource.name: resource for resource in template.resources}
    changes: list[PlanChange] = []
    unchanged = 0

    for desired in template.resources:
        current = current_by_name.get(desired.name)
        if current is None:
            changes.append(
                PlanChange(
                    action="create",
                    resource=desired,
                    reason="Resource is not present in the simulated state.",
                )
            )
            continue

        if _resource_changed(current, desired):
            changes.append(
                PlanChange(
                    action="update",
                    resource=desired,
                    reason="Resource differs from the latest deployed state.",
                )
            )
        else:
            unchanged += 1

    for current in current_by_name.values():
        if current.name not in desired_by_name:
            changes.append(
                PlanChange(
                    action="delete",
                    resource=current,
                    reason="Resource exists in the latest deployment but is absent from the new template.",
                )
            )

    total_cost = sum(resource.estimated_monthly_cost for resource in template.resources)
    summary = {
        "create": sum(1 for change in changes if change.action == "create"),
        "update": sum(1 for change in changes if change.action == "update"),
        "delete": sum(1 for change in changes if change.action == "delete"),
    }
    return DeploymentPlan(
        template_name=template.file_name,
        summary=summary,
        changes=changes,
        estimated_monthly_cost=total_cost,
        target_resources=template.resources,
        drift=DriftReport(
            creates=summary["create"],
            updates=summary["update"],
            deletes=summary["delete"],
            unchanged=unchanged,
        ),
        policy_violations=_policy_violations(template.resources),
    )


def create_deployment(plan: DeploymentPlan, project_id: str = "demo-azure-core") -> Deployment:
    steps = [
        DeploymentStep(name="Queued", status="success", logs=["Deployment request accepted."], sequence_order=1),
        DeploymentStep(name="Validate", status="success", logs=["IaC syntax and required fields passed."], sequence_order=2),
        DeploymentStep(name="Plan", status="success", logs=[f"{plan.summary['create']} create actions generated."], sequence_order=3),
        DeploymentStep(name="Deploy", status="success", logs=["Simulated Azure deployment completed."], sequence_order=4),
        DeploymentStep(name="Record History", status="success", logs=["Deployment version stored for rollback."], sequence_order=5),
    ]
    return Deployment(
        id=str(uuid.uuid4()),
        project_id=project_id,
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
                        dependencies=_extract_terraform_dependencies(config),
                        metadata=config if isinstance(config, dict) else {},
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
                metadata=item,
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
    metadata: Optional[dict[str, Any]] = None,
) -> Resource:
    return Resource(
        name=name,
        type=resource_type,
        region=region,
        dependencies=dependencies or [],
        estimated_monthly_cost=COST_BY_TYPE.get(resource_type, 8),
        metadata=metadata or {},
    )


def _extract_terraform_dependencies(config: Any) -> list[str]:
    dependencies: list[str] = []
    _collect_terraform_dependencies(config, dependencies)
    return list(dict.fromkeys(dependencies))


def _collect_terraform_dependencies(value: Any, dependencies: list[str]) -> None:
    if isinstance(value, str):
        for _, resource_name in TERRAFORM_REFERENCE_PATTERN.findall(value):
            dependencies.append(resource_name)
        return

    if isinstance(value, list):
        for item in value:
            _collect_terraform_dependencies(item, dependencies)
        return

    if isinstance(value, dict):
        for item in value.values():
            _collect_terraform_dependencies(item, dependencies)


def _resource_changed(current: Resource, desired: Resource) -> bool:
    return (
        current.type != desired.type
        or current.region != desired.region
        or current.dependencies != desired.dependencies
        or current.estimated_monthly_cost != desired.estimated_monthly_cost
        or current.metadata != desired.metadata
    )


def _policy_violations(resources: list[Resource]) -> list[PolicyViolation]:
    violations = []
    for resource in resources:
        metadata = resource.metadata
        public_access = metadata.get("public_access") or metadata.get("allow_public_access")

        if resource.type in {"azurerm_public_ip", "public_ip"} or public_access is True:
            violations.append(
                PolicyViolation(
                    rule_id="POLICY_PUBLIC_RESOURCE",
                    severity="high",
                    resource_name=resource.name,
                    resource_type=resource.type,
                    message="Publicly reachable resources require review before deployment.",
                )
            )

        if resource.estimated_monthly_cost >= 50:
            violations.append(
                PolicyViolation(
                    rule_id="POLICY_EXPENSIVE_RESOURCE",
                    severity="medium",
                    resource_name=resource.name,
                    resource_type=resource.type,
                    message="Estimated monthly cost is above the portfolio policy threshold.",
                )
            )

        tags = metadata.get("tags")
        if resource.type not in {"resource_group", "azurerm_resource_group"} and isinstance(tags, dict) and not tags:
            violations.append(
                PolicyViolation(
                    rule_id="POLICY_EMPTY_TAGS",
                    severity="low",
                    resource_name=resource.name,
                    resource_type=resource.type,
                    message="Resource has an empty tag set.",
                )
            )
    return violations
