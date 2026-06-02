from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.models import User
from app.schemas.auth import AuthCredentials, TokenResponse
from app.schemas.deployment import Deployment, DeploymentPlan, TemplateValidation
from app.schemas.project import ProjectCreate, ProjectRead
from app.schemas.resource import CostEstimate, PersistedResource
from app.schemas.template import TemplateRead, TemplateUploadResult
from app.core.database import get_db
from app.services.auth import authenticate_user, create_user, get_user_by_email, token_for_user
from app.services.deployments import deploy_template, get_deployment, list_deployments
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


@router.post("/auth/register", response_model=TokenResponse, status_code=201)
def register(credentials: AuthCredentials, db: Session = Depends(get_db)) -> TokenResponse:
    if get_user_by_email(db, credentials.email) is not None:
        raise HTTPException(status_code=409, detail="Email is already registered.")
    user = create_user(db, credentials)
    return token_for_user(user)


@router.post("/auth/login", response_model=TokenResponse)
def login(credentials: AuthCredentials, db: Session = Depends(get_db)) -> TokenResponse:
    user = authenticate_user(db, credentials)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return token_for_user(user)


@router.get("/projects", response_model=list[ProjectRead])
def get_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ProjectRead]:
    return list_projects(db, current_user.id)


@router.post("/projects", response_model=ProjectRead, status_code=201)
def post_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectRead:
    return create_project(db, payload, current_user.id)


@router.get("/projects/{project_id}", response_model=ProjectRead)
def get_project_by_id(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectRead:
    project = get_project(db, project_id, current_user.id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project


@router.get("/projects/{project_id}/deployments")
def get_project_deployments(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Deployment]:
    if get_project(db, project_id, current_user.id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return list_deployments(db, project_id)


@router.get("/deployments/{deployment_id}", response_model=Deployment)
def get_deployment_by_id(
    deployment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Deployment:
    deployment = get_deployment(db, deployment_id)
    if deployment is None or get_project(db, deployment.project_id, current_user.id) is None:
        raise HTTPException(status_code=404, detail="Deployment not found.")
    return deployment


@router.get("/projects/{project_id}/templates", response_model=list[TemplateRead])
def get_project_templates(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TemplateRead]:
    if get_project(db, project_id, current_user.id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return list_templates(db, project_id)


@router.get("/projects/{project_id}/resources", response_model=list[PersistedResource])
def get_project_resources(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PersistedResource]:
    if get_project(db, project_id, current_user.id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return list_project_resources(db, project_id)


@router.get("/projects/{project_id}/cost-estimate", response_model=CostEstimate)
def get_project_cost(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CostEstimate:
    if get_project(db, project_id, current_user.id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return get_project_cost_estimate(db, project_id)


@router.post("/projects/{project_id}/templates/upload", response_model=TemplateUploadResult, status_code=201)
async def upload_project_template(
    project_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TemplateUploadResult:
    if get_project(db, project_id, current_user.id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    content = (await file.read()).decode("utf-8")
    parsed = parse_template_content(file.filename or "template", content)
    if not parsed.resources:
        raise HTTPException(status_code=422, detail="No resources found in template.")

    template = create_template(db, project_id=project_id, raw_content=content, parsed=parsed)
    return TemplateUploadResult(template=template, resources=parsed.resources, warnings=[])


@router.post("/templates/{template_id}/plan", response_model=DeploymentPlan)
def plan_saved_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeploymentPlan:
    template = get_template(db, template_id)
    if template is None or get_project(db, template.project_id, current_user.id) is None:
        raise HTTPException(status_code=404, detail="Template not found.")

    plan = get_template_plan(db, template_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Template not found.")
    return plan


@router.post("/templates/{template_id}/deploy", response_model=Deployment, status_code=201)
def deploy_saved_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Deployment:
    template = get_template(db, template_id)
    if template is None or get_project(db, template.project_id, current_user.id) is None:
        raise HTTPException(status_code=404, detail="Template not found.")

    deployment = deploy_template(db, template_id)
    if deployment is None:
        raise HTTPException(status_code=404, detail="Template not found.")
    return deployment


@router.post("/templates/validate", response_model=TemplateValidation)
async def validate_uploaded_template(file: UploadFile = File(...)) -> TemplateValidation:
    content = (await file.read()).decode("utf-8")
    return validate_template(file.filename or "template", content)


@router.post("/templates/plan", response_model=DeploymentPlan)
async def plan_uploaded_template(file: UploadFile = File(...)) -> DeploymentPlan:
    content = (await file.read()).decode("utf-8")
    parsed = parse_template_content(file.filename or "template", content)
    if not parsed.resources:
        raise HTTPException(status_code=422, detail="No resources found in template.")
    return generate_plan(parsed)


@router.post("/templates/deploy", response_model=Deployment)
async def deploy_uploaded_template(file: UploadFile = File(...)) -> Deployment:
    content = (await file.read()).decode("utf-8")
    parsed = parse_template_content(file.filename or "template", content)
    if not parsed.resources:
        raise HTTPException(status_code=422, detail="No resources found in template.")
    plan = generate_plan(parsed)
    return create_deployment(plan)
