from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Resource(BaseModel):
    name: str
    type: str
    provider: str = "azure"
    region: str = "eastus"
    dependencies: list[str] = Field(default_factory=list)
    estimated_monthly_cost: float = 0


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


class DeploymentPlan(BaseModel):
    template_name: str
    summary: dict[str, int]
    changes: list[PlanChange]
    estimated_monthly_cost: float


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
