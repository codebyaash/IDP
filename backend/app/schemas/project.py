from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProjectBase(BaseModel):
    name: str
    cloud_provider: str = "azure"
    environment: str = "dev"


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    monthly_cost: float
    created_at: datetime
