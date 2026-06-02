from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy import inspect, text

from app.api.routes import router
from app.core.database import Base, SessionLocal, engine
from app import models
from app.services.projects import seed_demo_user_and_project


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_local_schema()
    with SessionLocal() as db:
        seed_demo_user_and_project(db)
    yield


def ensure_local_schema() -> None:
    inspector = inspect(engine)
    if "projects" not in inspector.get_table_names():
        return

    project_columns = {column["name"] for column in inspector.get_columns("projects")}
    template_columns = set()
    deployment_columns = set()
    resource_columns = set()
    rollback_columns = set()
    table_names = inspector.get_table_names()
    if "iac_templates" in table_names:
        template_columns = {column["name"] for column in inspector.get_columns("iac_templates")}
    if "deployments" in table_names:
        deployment_columns = {column["name"] for column in inspector.get_columns("deployments")}
    if "resources" in inspector.get_table_names():
        resource_columns = {column["name"] for column in inspector.get_columns("resources")}
    if "rollback_events" in table_names:
        rollback_columns = {column["name"] for column in inspector.get_columns("rollback_events")}

    with engine.begin() as connection:
        if "user_id" not in project_columns:
            connection.execute(text("ALTER TABLE projects ADD COLUMN user_id VARCHAR"))
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


app = FastAPI(
    title="DeployForge API",
    summary="Simulation-first infrastructure deployment platform API.",
    description=(
        "DeployForge provides portfolio-safe infrastructure workflows: upload IaC templates, "
        "validate and plan changes, simulate environment-aware deployments, inspect resource graphs, "
        "estimate monthly cost, and roll back to previous deployment snapshots."
    ),
    version="0.1.0",
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
        {"name": "System", "description": "Health checks and API metadata."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health", tags=["System"], summary="Check API health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "deployforge-api"}


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")
