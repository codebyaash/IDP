from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuthCredentials(BaseModel):
    email: str
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    organization_id: str
    organization_name: str
    created_at: datetime


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    action: str
    entity_type: str
    entity_id: str | None
    project_id: str | None
    environment: str | None
    message: str
    metadata_json: dict[str, Any]
    created_at: datetime


class ProfileRead(BaseModel):
    user: UserRead
    activity: list[AuditLogRead]
    organization_activity: list[AuditLogRead]
    summary: dict[str, int]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
