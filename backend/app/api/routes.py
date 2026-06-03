from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.models import User
from app.schemas.auth import AuthCredentials, ProfileRead, TokenResponse, UserRead
from app.schemas.deployment import Deployment, DeploymentPlan, TemplateValidation
from app.schemas.project import DeploymentEnvironment, ProjectCreate, ProjectRead
from app.schemas.resource import CostEstimate, PersistedResource
from app.schemas.rollback import RollbackRequest, RollbackResult
from app.schemas.template import TemplateRead, TemplateUploadResult
from app.core.database import get_db
from app.services.audit import list_organization_activity, list_user_activity, log_activity, user_activity_summary
from app.services.auth import authenticate_user, create_user, get_user_by_email, token_for_user
from app.services.deployments import deploy_template, get_deployment, list_deployments, rollback_deployment
from app.services.projects import create_project, get_project, list_projects
from app.services.resources import get_project_cost_estimate, list_project_resources
from app.services.simulator import (
    create_deployment,
    generate_plan,
    parse_template_content,
    validate_template,
)
from app.services.templates import create_template, get_template, get_template_plan, list_templates

router = APIRouter(prefix="/api")


def _parse_uploaded_template(file_name: str, content: str):
    try:
        parsed = parse_template_content(file_name, content)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if not parsed.resources:
        raise HTTPException(status_code=422, detail="No resources found in template.")

    duplicate_names = _duplicate_resource_names([resource.name for resource in parsed.resources])
    if duplicate_names:
        raise HTTPException(
            status_code=422,
            detail=f"Duplicate resource names are not allowed: {', '.join(duplicate_names)}.",
        )

    return parsed


def _duplicate_resource_names(resource_names: list[str]) -> list[str]:
    seen = set()
    duplicates = []
    for name in resource_names:
        if name in seen and name not in duplicates:
            duplicates.append(name)
        seen.add(name)
    return duplicates


@router.post("/auth/register", response_model=TokenResponse, status_code=201, tags=["Auth"], summary="Register a user")
def register(credentials: AuthCredentials, db: Session = Depends(get_db)) -> TokenResponse:
    if get_user_by_email(db, credentials.email) is not None:
        raise HTTPException(status_code=409, detail="Email is already registered.")
    user = create_user(db, credentials)
    log_activity(
        db,
        user,
        "registered",
        "user",
        "User joined the organization workspace.",
        entity_id=user.id,
    )
    return token_for_user(user)


@router.post("/auth/login", response_model=TokenResponse, tags=["Auth"], summary="Login and receive a JWT")
def login(credentials: AuthCredentials, db: Session = Depends(get_db)) -> TokenResponse:
    user = authenticate_user(db, credentials)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    log_activity(db, user, "logged_in", "user", "User signed in.", entity_id=user.id)
    return token_for_user(user)


@router.get("/me", response_model=ProfileRead, tags=["Profile"], summary="Get current user profile")
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProfileRead:
    return ProfileRead(
        user=UserRead.model_validate(current_user),
        activity=list_user_activity(db, current_user.id),
        organization_activity=list_organization_activity(db, current_user.organization_id),
        summary=user_activity_summary(db, current_user.id),
    )


@router.get("/projects", response_model=list[ProjectRead], tags=["Projects"], summary="List projects")
def get_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ProjectRead]:
    return list_projects(db, current_user.organization_id)


@router.post("/projects", response_model=ProjectRead, status_code=201, tags=["Projects"], summary="Create a project")
def post_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectRead:
    project = create_project(db, payload, current_user)
    log_activity(
        db,
        current_user,
        "created_project",
        "project",
        f"Created project {project.name}.",
        entity_id=project.id,
        project_id=project.id,
        environment=project.environment,
    )
    return project


@router.get("/projects/{project_id}", response_model=ProjectRead, tags=["Projects"], summary="Get a project")
def get_project_by_id(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectRead:
    project = get_project(db, project_id, current_user.organization_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project


@router.get(
    "/projects/{project_id}/deployments",
    response_model=list[Deployment],
    tags=["Deployments"],
    summary="List deployment history",
)
def get_project_deployments(
    project_id: str,
    environment: DeploymentEnvironment = Query("dev", description="Deployment environment to read: dev, stage, or prod."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Deployment]:
    if get_project(db, project_id, current_user.organization_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return list_deployments(db, project_id, environment)


@router.get("/deployments/{deployment_id}", response_model=Deployment, tags=["Deployments"], summary="Get a deployment")
def get_deployment_by_id(
    deployment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Deployment:
    deployment = get_deployment(db, deployment_id)
    if deployment is None or get_project(db, deployment.project_id, current_user.organization_id) is None:
        raise HTTPException(status_code=404, detail="Deployment not found.")
    return deployment


@router.post(
    "/deployments/{deployment_id}/rollback",
    response_model=RollbackResult,
    status_code=201,
    tags=["Deployments"],
    summary="Rollback a deployment",
)
def rollback_deployment_by_id(
    deployment_id: str,
    payload: RollbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RollbackResult:
    deployment = get_deployment(db, deployment_id)
    if deployment is None or get_project(db, deployment.project_id, current_user.organization_id) is None:
        raise HTTPException(status_code=404, detail="Deployment not found.")

    result = rollback_deployment(db, deployment_id, payload.reason)
    if result is None:
        raise HTTPException(status_code=422, detail="Deployment cannot be rolled back.")
    log_activity(
        db,
        current_user,
        "rolled_back_deployment",
        "deployment",
        f"Rolled back deployment {deployment_id}.",
        entity_id=result.rollback_deployment.id,
        project_id=result.rollback_deployment.project_id,
        environment=result.rollback_deployment.environment,
        metadata={"source_deployment_id": deployment_id, "reason": payload.reason},
    )
    return result


@router.get(
    "/projects/{project_id}/templates",
    response_model=list[TemplateRead],
    tags=["Templates"],
    summary="List saved templates",
)
def get_project_templates(
    project_id: str,
    environment: DeploymentEnvironment = Query("dev", description="Deployment environment to read: dev, stage, or prod."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TemplateRead]:
    if get_project(db, project_id, current_user.organization_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return list_templates(db, project_id, environment)


@router.get(
    "/projects/{project_id}/resources",
    response_model=list[PersistedResource],
    tags=["Resources"],
    summary="List latest resources",
)
def get_project_resources(
    project_id: str,
    environment: DeploymentEnvironment = Query("dev", description="Deployment environment to read: dev, stage, or prod."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PersistedResource]:
    if get_project(db, project_id, current_user.organization_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return list_project_resources(db, project_id, environment)


@router.get(
    "/projects/{project_id}/cost-estimate",
    response_model=CostEstimate,
    tags=["Resources"],
    summary="Get latest cost estimate",
)
def get_project_cost(
    project_id: str,
    environment: DeploymentEnvironment = Query("dev", description="Deployment environment to read: dev, stage, or prod."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CostEstimate:
    if get_project(db, project_id, current_user.organization_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return get_project_cost_estimate(db, project_id, environment)


@router.post(
    "/projects/{project_id}/templates/upload",
    response_model=TemplateUploadResult,
    status_code=201,
    tags=["Templates"],
    summary="Upload an IaC template",
)
async def upload_project_template(
    project_id: str,
    environment: DeploymentEnvironment = Form(
        "dev",
        description="Deployment environment to store this template under: dev, stage, or prod.",
    ),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TemplateUploadResult:
    if get_project(db, project_id, current_user.organization_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    content = (await file.read()).decode("utf-8")
    parsed = _parse_uploaded_template(file.filename or "template", content)

    template = create_template(db, project_id=project_id, raw_content=content, parsed=parsed, environment=environment)
    log_activity(
        db,
        current_user,
        "uploaded_template",
        "template",
        f"Uploaded template {template.file_name}.",
        entity_id=template.id,
        project_id=project_id,
        environment=environment,
        metadata={"resource_count": len(parsed.resources), "version": template.version},
    )
    return TemplateUploadResult(template=template, resources=parsed.resources, warnings=[])


@router.post(
    "/templates/{template_id}/plan",
    response_model=DeploymentPlan,
    tags=["Templates"],
    summary="Generate a saved-template deployment plan",
)
def plan_saved_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeploymentPlan:
    template = get_template(db, template_id)
    if template is None or get_project(db, template.project_id, current_user.organization_id) is None:
        raise HTTPException(status_code=404, detail="Template not found.")

    plan = get_template_plan(db, template_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Template not found.")
    return plan


@router.post(
    "/templates/{template_id}/deploy",
    response_model=Deployment,
    status_code=201,
    tags=["Deployments"],
    summary="Deploy a saved template",
)
def deploy_saved_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Deployment:
    template = get_template(db, template_id)
    if template is None or get_project(db, template.project_id, current_user.organization_id) is None:
        raise HTTPException(status_code=404, detail="Template not found.")

    deployment = deploy_template(db, template_id)
    if deployment is None:
        raise HTTPException(status_code=404, detail="Template not found.")
    log_activity(
        db,
        current_user,
        "deployed_template",
        "deployment",
        f"Ran deployment for {template.file_name}.",
        entity_id=deployment.id,
        project_id=deployment.project_id,
        environment=deployment.environment,
        metadata={"template_id": template.id, "monthly_cost": deployment.plan.estimated_monthly_cost},
    )
    return deployment


@router.post(
    "/templates/validate",
    response_model=TemplateValidation,
    tags=["Templates"],
    summary="Validate an uploaded template",
)
async def validate_uploaded_template(file: UploadFile = File(...)) -> TemplateValidation:
    content = (await file.read()).decode("utf-8")
    return validate_template(file.filename or "template", content)


@router.post(
    "/templates/plan",
    response_model=DeploymentPlan,
    tags=["Templates"],
    summary="Plan an uploaded template without saving it",
)
async def plan_uploaded_template(file: UploadFile = File(...)) -> DeploymentPlan:
    content = (await file.read()).decode("utf-8")
    parsed = _parse_uploaded_template(file.filename or "template", content)
    return generate_plan(parsed)


@router.post(
    "/templates/deploy",
    response_model=Deployment,
    tags=["Deployments"],
    summary="Deploy an uploaded template without saving it",
)
async def deploy_uploaded_template(file: UploadFile = File(...)) -> Deployment:
    content = (await file.read()).decode("utf-8")
    parsed = _parse_uploaded_template(file.filename or "template", content)
    plan = generate_plan(parsed)
    return create_deployment(plan)
