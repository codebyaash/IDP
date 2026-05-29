from pydantic import BaseModel


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


class CostBreakdownItem(BaseModel):
    label: str
    monthly_cost: float
    resource_count: int


class CostEstimate(BaseModel):
    project_id: str
    total_monthly_cost: float
    resource_count: int
    breakdown: list[CostBreakdownItem]
