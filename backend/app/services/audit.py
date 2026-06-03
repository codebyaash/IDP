from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AuditLog, User


def log_activity(
    db: Session,
    user: User,
    action: str,
    entity_type: str,
    message: str,
    *,
    entity_id: Optional[str] = None,
    project_id: Optional[str] = None,
    environment: Optional[str] = None,
    metadata: Optional[dict] = None,
    commit: bool = True,
) -> AuditLog:
    entry = AuditLog(
        user_id=user.id,
        organization_id=user.organization_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        project_id=project_id,
        environment=environment,
        message=message,
        metadata_json=metadata or {},
    )
    db.add(entry)
    if commit:
        db.commit()
        db.refresh(entry)
    return entry


def list_user_activity(db: Session, user_id: str, limit: int = 50) -> list[AuditLog]:
    statement = (
        select(AuditLog)
        .where(AuditLog.user_id == user_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(statement))


def list_organization_activity(db: Session, organization_id: str, limit: int = 50) -> list[AuditLog]:
    statement = (
        select(AuditLog)
        .where(AuditLog.organization_id == organization_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(statement))


def user_activity_summary(db: Session, user_id: str) -> dict[str, int]:
    rows = db.execute(
        select(AuditLog.action, func.count(AuditLog.id)).where(AuditLog.user_id == user_id).group_by(AuditLog.action)
    )
    return {action: count for action, count in rows}
