from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.schemas.deployment import Resource


class TemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    environment: str
    file_name: str
    file_type: str
    version: int
    parsed_json: dict[str, Any]
    created_at: datetime


class TemplateUploadResult(BaseModel):
    template: TemplateRead
    resources: list[Resource]
    warnings: list[str] = []
