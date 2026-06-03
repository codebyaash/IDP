from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy import inspect, text

from app.api.routes import router
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app import models
from app.services.projects import seed_demo_user_and_project


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)
    if settings.repair_local_schema and settings.sqlalchemy_database_url.startswith("sqlite"):
        ensure_local_schema()
    if settings.seed_demo_data:
        with SessionLocal() as db:
            seed_demo_user_and_project(db)
    yield


def ensure_local_schema() -> None:
    inspector = inspect(engine)
    if "projects" not in inspector.get_table_names():
        return

    project_columns = {column["name"] for column in inspector.get_columns("projects")}
    user_columns = set()
    template_columns = set()
    deployment_columns = set()
    resource_columns = set()
    rollback_columns = set()
    table_names = inspector.get_table_names()
    if "iac_templates" in table_names:
        template_columns = {column["name"] for column in inspector.get_columns("iac_templates")}
    if "users" in table_names:
        user_columns = {column["name"] for column in inspector.get_columns("users")}
    if "deployments" in table_names:
        deployment_columns = {column["name"] for column in inspector.get_columns("deployments")}
    if "resources" in inspector.get_table_names():
        resource_columns = {column["name"] for column in inspector.get_columns("resources")}
    if "rollback_events" in table_names:
        rollback_columns = {column["name"] for column in inspector.get_columns("rollback_events")}

    with engine.begin() as connection:
        if "users" in table_names and "organization_id" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN organization_id VARCHAR DEFAULT 'deployforge.local' NOT NULL"))
        if "users" in table_names and "organization_name" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN organization_name VARCHAR DEFAULT 'Deployforge' NOT NULL"))
        if "user_id" not in project_columns:
            connection.execute(text("ALTER TABLE projects ADD COLUMN user_id VARCHAR"))
        if "organization_id" not in project_columns:
            connection.execute(text("ALTER TABLE projects ADD COLUMN organization_id VARCHAR DEFAULT 'deployforge.local' NOT NULL"))
        if "iac_templates" in table_names and "environment" not in template_columns:
            connection.execute(text("ALTER TABLE iac_templates ADD COLUMN environment VARCHAR DEFAULT 'dev'"))
        if "deployments" in table_names and "environment" not in deployment_columns:
            connection.execute(text("ALTER TABLE deployments ADD COLUMN environment VARCHAR DEFAULT 'dev'"))
        if "resources" in table_names and "environment" not in resource_columns:
            connection.execute(text("ALTER TABLE resources ADD COLUMN environment VARCHAR DEFAULT 'dev'"))
        if "resources" in table_names and "resource_metadata" not in resource_columns:
            connection.execute(text("ALTER TABLE resources ADD COLUMN resource_metadata JSON DEFAULT '{}'"))
        if "rollback_events" in table_names and "environment" not in rollback_columns:
            connection.execute(text("ALTER TABLE rollback_events ADD COLUMN environment VARCHAR DEFAULT 'dev'"))
        connection.execute(
            text(
                "UPDATE projects SET organization_id = "
                "COALESCE((SELECT users.organization_id FROM users WHERE users.id = projects.user_id), organization_id)"
            )
        )


app = FastAPI(
    title=settings.app_name,
    summary="Simulation-first infrastructure deployment platform API.",
    description=(
        "DeployForge provides portfolio-safe infrastructure workflows: upload IaC templates, "
        "validate and plan changes, simulate environment-aware deployments, inspect resource graphs, "
        "estimate monthly cost, and roll back to previous deployment snapshots."
    ),
    version=settings.app_version,
    lifespan=lifespan,
    contact={
        "name": "DeployForge Portfolio API",
        "url": "http://localhost:3001",
    },
    swagger_ui_parameters={
        "defaultModelsExpandDepth": 1,
        "displayRequestDuration": True,
        "docExpansion": "none",
        "persistAuthorization": True,
        "tryItOutEnabled": True,
    },
    openapi_tags=[
        {"name": "Auth", "description": "Register, login, and issue JWT bearer tokens."},
        {"name": "Projects", "description": "Create and list cloud infrastructure workspaces."},
        {"name": "Templates", "description": "Upload, validate, and plan IaC templates."},
        {"name": "Deployments", "description": "Run simulated deployment pipelines and rollback snapshots."},
        {"name": "Resources", "description": "Inspect latest environment-scoped resources and cost estimates."},
        {"name": "Profile", "description": "Read current user details and audit activity."},
        {"name": "System", "description": "Health checks and API metadata."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health", tags=["System"], summary="Check API health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "deployforge-api", "environment": settings.app_env}


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")
