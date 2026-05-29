from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.services.projects import seed_demo_project


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
        seed_demo_project(db)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_list_projects_includes_seed_project(client: TestClient) -> None:
    response = client.get("/api/projects")

    assert response.status_code == 200
    projects = response.json()
    assert any(project["id"] == "demo-azure-core" for project in projects)


def test_create_project(client: TestClient) -> None:
    response = client.post(
        "/api/projects",
        json={"name": "Payments Platform", "cloud_provider": "azure", "environment": "stage"},
    )

    assert response.status_code == 201
    project = response.json()
    assert project["name"] == "Payments Platform"
    assert project["environment"] == "stage"
    assert project["status"] == "healthy"


def test_upload_and_list_project_template(client: TestClient) -> None:
    template = """
resource "azurerm_resource_group" "core" {
  name     = "rg-deployforge-test"
  location = "eastus"
}
"""

    upload = client.post(
        "/api/projects/demo-azure-core/templates/upload",
        files={"file": ("main.tf", template, "text/plain")},
    )

    assert upload.status_code == 201
    payload = upload.json()
    assert payload["template"]["file_name"] == "main.tf"
    assert payload["template"]["version"] == 1
    assert len(payload["resources"]) == 1

    listing = client.get("/api/projects/demo-azure-core/templates")

    assert listing.status_code == 200
    templates = listing.json()
    assert templates[0]["file_name"] == "main.tf"


def test_generate_plan_from_saved_template(client: TestClient) -> None:
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
    )
    template_id = upload.json()["template"]["id"]

    plan = client.post(f"/api/templates/{template_id}/plan")

    assert plan.status_code == 200
    payload = plan.json()
    assert payload["summary"]["create"] == 2
    assert payload["estimated_monthly_cost"] == 12
    assert payload["changes"][1]["resource"]["name"] == "stplantest001"
