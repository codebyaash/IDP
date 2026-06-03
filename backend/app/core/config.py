import os

from pydantic import BaseModel, Field


def _bool_from_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _list_from_env(name: str, default: list[str]) -> list[str]:
    value = os.getenv(name)
    if value is None:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseModel):
    app_env: str = Field(default_factory=lambda: os.getenv("APP_ENV", "local"))
    app_name: str = Field(default_factory=lambda: os.getenv("APP_NAME", "DeployForge API"))
    app_version: str = Field(default_factory=lambda: os.getenv("APP_VERSION", "0.1.0"))
    database_url: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./deployforge.db"))
    secret_key: str = Field(default_factory=lambda: os.getenv("SECRET_KEY", "deployforge-local-dev-secret"))
    access_token_expire_minutes: int = Field(
        default_factory=lambda: int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 8)))
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: _list_from_env(
            "CORS_ORIGINS",
            ["http://localhost:3000", "http://localhost:3001"],
        )
    )
    seed_demo_data: bool = Field(default_factory=lambda: _bool_from_env("SEED_DEMO_DATA", True))
    auto_create_tables: bool = Field(default_factory=lambda: _bool_from_env("AUTO_CREATE_TABLES", True))
    repair_local_schema: bool = Field(default_factory=lambda: _bool_from_env("REPAIR_LOCAL_SCHEMA", True))

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        if self.database_url.startswith("postgres://"):
            return self.database_url.replace("postgres://", "postgresql+psycopg://", 1)
        return self.database_url

    def validate_production(self) -> None:
        if not self.is_production:
            return
        if self.secret_key == "deployforge-local-dev-secret":
            raise RuntimeError("SECRET_KEY must be set to a unique value in production.")
        if self.auto_create_tables:
            raise RuntimeError("AUTO_CREATE_TABLES must be disabled in production. Run Alembic migrations instead.")
        if self.seed_demo_data:
            raise RuntimeError("SEED_DEMO_DATA must be disabled in production.")


settings = Settings()
settings.validate_production()
