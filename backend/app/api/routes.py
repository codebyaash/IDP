from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.schemas.deployment import Deployment, DeploymentPlan, TemplateValidation
from app.schemas.project import ProjectCreate, ProjectRead
from app.schemas.template import TemplateRead, TemplateUploadResult
from app.core.database import get_db
from app.services.projects import create_project, get_project, list_projects
from app.services.simulator import (
    create_deployment,
    generate_plan,
    list_sample_deployments,
    parse_template_content,
    validate_template,
)
from app.services.templates import create_template, list_templates

router = APIRouter(prefix="/api")


@router.get("/projects", response_model=list[ProjectRead])
def get_projects(db: Session = Depends(get_db)) -> list[ProjectRead]:
    return list_projects(db)


@router.post("/projects", response_model=ProjectRead, status_code=201)
def post_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> ProjectRead:
    return create_project(db, payload)


@router.get("/projects/{project_id}", response_model=ProjectRead)
def get_project_by_id(project_id: str, db: Session = Depends(get_db)) -> ProjectRead:
    project = get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project


@router.get("/projects/{project_id}/deployments")
def get_project_deployments(project_id: str, db: Session = Depends(get_db)) -> list[Deployment]:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return list_sample_deployments(project_id)


@router.get("/projects/{project_id}/templates", response_model=list[TemplateRead])
def get_project_templates(project_id: str, db: Session = Depends(get_db)) -> list[TemplateRead]:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return list_templates(db, project_id)


@router.post("/projects/{project_id}/templates/upload", response_model=TemplateUploadResult, status_code=201)
async def upload_project_template(
    project_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> TemplateUploadResult:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    content = (await file.read()).decode("utf-8")
    parsed = parse_template_content(file.filename or "template", content)
    if not parsed.resources:
        raise HTTPException(status_code=422, detail="No resources found in template.")

    template = create_template(db, project_id=project_id, raw_content=content, parsed=parsed)
    return TemplateUploadResult(template=template, resources=parsed.resources, warnings=[])


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
