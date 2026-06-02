from pydantic import BaseModel

from app.schemas.deployment import Deployment


class RollbackRequest(BaseModel):
    reason: str = "Manual rollback"


class RollbackResult(BaseModel):
    source_deployment_id: str
    rollback_deployment: Deployment
