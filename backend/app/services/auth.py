from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.schemas.auth import AuthCredentials, TokenResponse, UserRead


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.scalar(select(User).where(User.email == email.lower()))


def create_user(db: Session, credentials: AuthCredentials) -> User:
    user = User(email=credentials.email.lower(), password_hash=hash_password(credentials.password))
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
        user=UserRead(id=user.id, email=user.email),
    )
