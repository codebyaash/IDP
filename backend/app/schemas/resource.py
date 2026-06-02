from pydantic import BaseModel, Field


class PersistedResource(BaseModel):
    id: str
    deployment_id: str
    project_id: str
    resource_name: str
    resource_type: str
    provider: str
    region: str
    dependencies: list[str]
    estimated_monthly_cost: float
    resource_metadata: dict = Field(default_factory=dict)


class CostBreakdownItem(BaseModel):
    label: str
    monthly_cost: float
    resource_count: int


class CostEstimate(BaseModel):
    project_id: str
    total_monthly_cost: float
    resource_count: int
    breakdown: list[CostBreakdownItem]
