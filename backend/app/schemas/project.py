from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

DeploymentEnvironment = Literal["dev", "stage", "prod"]


class ProjectBase(BaseModel):
    name: str
    cloud_provider: str = "azure"
    environment: DeploymentEnvironment = "dev"


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    status: str
    monthly_cost: float
    created_at: datetime
