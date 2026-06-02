from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class Resource(BaseModel):
    name: str
    type: str
    provider: str = "azure"
    region: str = "eastus"
    dependencies: list[str] = Field(default_factory=list)
    estimated_monthly_cost: float = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class ParsedTemplate(BaseModel):
    file_name: str
    file_type: str
    resources: list[Resource]


class TemplateValidation(BaseModel):
    file_name: str
    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    resources_found: int = 0


class PlanChange(BaseModel):
    action: str
    resource: Resource
    reason: str


class DriftReport(BaseModel):
    creates: int = 0
    updates: int = 0
    deletes: int = 0
    unchanged: int = 0


class PolicyViolation(BaseModel):
    rule_id: str
    severity: str
    resource_name: str
    resource_type: str
    message: str


class DeploymentPlan(BaseModel):
    template_name: str
    summary: dict[str, int]
    changes: list[PlanChange]
    estimated_monthly_cost: float
    target_resources: list[Resource] = Field(default_factory=list)
    drift: DriftReport = Field(default_factory=DriftReport)
    policy_violations: list[PolicyViolation] = Field(default_factory=list)


class DeploymentStep(BaseModel):
    name: str
    status: str
    logs: list[str]
    sequence_order: int


class Deployment(BaseModel):
    id: str
    project_id: str
    status: str
    plan: DeploymentPlan
    steps: list[DeploymentStep]
    created_at: Optional[datetime] = None
