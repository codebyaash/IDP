from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.schemas.auth import AuthCredentials, TokenResponse, UserRead


def organization_from_email(email: str) -> tuple[str, str]:
    normalized = email.lower().strip()
    domain = normalized.split("@", 1)[1] if "@" in normalized else "personal"
    label = domain.split(".", 1)[0].replace("-", " ").replace("_", " ").title()
    return domain, label or domain


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.scalar(select(User).where(User.email == email.lower()))


def create_user(db: Session, credentials: AuthCredentials) -> User:
    email = credentials.email.lower().strip()
    organization_id, organization_name = organization_from_email(email)
    user = User(
        email=email,
        organization_id=organization_id,
        organization_name=organization_name,
        password_hash=hash_password(credentials.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, credentials: AuthCredentials) -> Optional[User]:
    user = get_user_by_email(db, credentials.email)
    if user is None or not verify_password(credentials.password, user.password_hash):
        return None
    return user


def token_for_user(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id),
        user=UserRead(
            id=user.id,
            email=user.email,
            organization_id=user.organization_id,
            organization_name=user.organization_name,
            created_at=user.created_at,
        ),
    )
