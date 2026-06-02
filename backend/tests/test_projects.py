from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.services.projects import DEMO_USER_EMAIL, DEMO_USER_PASSWORD, seed_demo_user_and_project


@pytest.fixture
def client() -> TestClient:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        seed_demo_user_and_project(db)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"email": DEMO_USER_EMAIL, "password": DEMO_USER_PASSWORD},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_register_and_login(client: TestClient) -> None:
    register = client.post(
        "/api/auth/register",
        json={"email": "new-user@deployforge.local", "password": "strong-password"},
    )

    assert register.status_code == 201
    assert register.json()["token_type"] == "bearer"

    login = client.post(
        "/api/auth/login",
        json={"email": "new-user@deployforge.local", "password": "strong-password"},
    )

    assert login.status_code == 200
    assert login.json()["user"]["email"] == "new-user@deployforge.local"


def test_projects_require_auth(client: TestClient) -> None:
    response = client.get("/api/projects")

    assert response.status_code == 401


def test_list_projects_includes_seed_project(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/api/projects", headers=auth_headers)

    assert response.status_code == 200
    projects = response.json()
    assert any(project["id"] == "demo-azure-core" for project in projects)


def test_create_project(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/projects",
        json={"name": "Payments Platform", "cloud_provider": "azure", "environment": "stage"},
        headers=auth_headers,
    )

    assert response.status_code == 201
    project = response.json()
    assert project["name"] == "Payments Platform"
    assert project["environment"] == "stage"
    assert project["status"] == "healthy"


def test_upload_and_list_project_template(client: TestClient, auth_headers: dict[str, str]) -> None:
    template = """
resource "azurerm_resource_group" "core" {
  name     = "rg-deployforge-test"
  location = "eastus"
}
"""

    upload = client.post(
        "/api/projects/demo-azure-core/templates/upload",
        files={"file": ("main.tf", template, "text/plain")},
        headers=auth_headers,
    )

    assert upload.status_code == 201
    payload = upload.json()
    assert payload["template"]["file_name"] == "main.tf"
    assert payload["template"]["version"] == 1
    assert len(payload["resources"]) == 1

    listing = client.get("/api/projects/demo-azure-core/templates", headers=auth_headers)

    assert listing.status_code == 200
    templates = listing.json()
    assert templates[0]["file_name"] == "main.tf"


def test_generate_plan_from_saved_template(client: TestClient, auth_headers: dict[str, str]) -> None:
    template = """
resources:
  - name: rg-plan-test
    type: resource_group
    provider: azure
    region: eastus
  - name: stplantest001
    type: storage_account
    provider: azure
    region: eastus
    dependencies:
      - rg-plan-test
"""

    upload = client.post(
        "/api/projects/demo-azure-core/templates/upload",
        files={"file": ("storage.yaml", template, "text/yaml")},
        headers=auth_headers,
    )
    template_id = upload.json()["template"]["id"]

    plan = client.post(f"/api/templates/{template_id}/plan", headers=auth_headers)

    assert plan.status_code == 200
    payload = plan.json()
    assert payload["summary"]["create"] == 2
    assert payload["estimated_monthly_cost"] == 12
    assert payload["changes"][1]["resource"]["name"] == "stplantest001"


def test_deploy_saved_template_and_list_history(client: TestClient, auth_headers: dict[str, str]) -> None:
    template = """
resources:
  - name: rg-history-test
    type: resource_group
    provider: azure
    region: eastus
  - name: stdeployhistory001
    type: storage_account
    provider: azure
    region: eastus
    dependencies:
      - rg-history-test
"""

    upload = client.post(
        "/api/projects/demo-azure-core/templates/upload",
        files={"file": ("history.yaml", template, "text/yaml")},
        headers=auth_headers,
    )
    template_id = upload.json()["template"]["id"]

    deployment = client.post(f"/api/templates/{template_id}/deploy", headers=auth_headers)

    assert deployment.status_code == 201
    payload = deployment.json()
    assert payload["status"] == "success"
    assert payload["plan"]["summary"]["create"] == 2
    assert len(payload["steps"]) == 5

    history = client.get("/api/projects/demo-azure-core/deployments", headers=auth_headers)

    assert history.status_code == 200
    deployments = history.json()
    assert deployments[0]["id"] == payload["id"]
    assert deployments[0]["plan"]["estimated_monthly_cost"] == 12

    resources = client.get("/api/projects/demo-azure-core/resources", headers=auth_headers)

    assert resources.status_code == 200
    resource_payload = resources.json()
    assert len(resource_payload) == 2
    assert resource_payload[0]["deployment_id"] == payload["id"]
    assert any(resource["dependencies"] == ["rg-history-test"] for resource in resource_payload if resource["resource_name"] == "stdeployhistory001")

    cost = client.get("/api/projects/demo-azure-core/cost-estimate", headers=auth_headers)

    assert cost.status_code == 200
    cost_payload = cost.json()
    assert cost_payload["total_monthly_cost"] == 12
    assert cost_payload["resource_count"] == 2
    assert any(item["label"] == "storage_account" for item in cost_payload["breakdown"])
