from pydantic import BaseModel


class AuthCredentials(BaseModel):
    email: str
    password: str


class UserRead(BaseModel):
    id: str
    email: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
