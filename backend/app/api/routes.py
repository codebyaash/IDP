from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.deployment import Deployment, DeploymentPlan, TemplateValidation
from app.services.simulator import (
    create_deployment,
    generate_plan,
    list_projects,
    list_sample_deployments,
    parse_template_content,
    validate_template,
)

router = APIRouter(prefix="/api")


@router.get("/projects")
def get_projects() -> list[dict]:
    return list_projects()


@router.get("/projects/{project_id}/deployments")
def get_project_deployments(project_id: str) -> list[Deployment]:
    return list_sample_deployments(project_id)


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
