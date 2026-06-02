from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models import Project
from app.services.projects import DEMO_USER_EMAIL, DEMO_USER_PASSWORD, seed_demo_user_and_project


@pytest.fixture
def client() -> TestClient:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    event.listen(engine, "connect", _enable_sqlite_foreign_keys)
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


def _enable_sqlite_foreign_keys(dbapi_connection, connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


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


def test_invalid_project_environment_is_rejected(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/projects",
        json={"name": "Invalid Env", "cloud_provider": "azure", "environment": "qa"},
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_database_rejects_orphan_project() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    event.listen(engine, "connect", _enable_sqlite_foreign_keys)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        db.add(Project(user_id="missing-user", name="Orphan Project", cloud_provider="azure", environment="dev"))
        with pytest.raises(IntegrityError):
            db.commit()


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


def test_invalid_template_environment_is_rejected(client: TestClient, auth_headers: dict[str, str]) -> None:
    upload = client.post(
        "/api/projects/demo-azure-core/templates/upload",
        data={"environment": "qa"},
        files={"file": ("main.tf", 'resource "azurerm_resource_group" "core" {}', "text/plain")},
        headers=auth_headers,
    )

    assert upload.status_code == 422


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
    assert payload["environment"] == "dev"
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


def test_rollback_restores_previous_deployment_resources(client: TestClient, auth_headers: dict[str, str]) -> None:
    first_template = """
resources:
  - name: rg-rollback-test
    type: resource_group
    provider: azure
    region: eastus
  - name: strollback001
    type: storage_account
    provider: azure
    region: eastus
"""
    second_template = """
resources:
  - name: rg-rollback-test
    type: resource_group
    provider: azure
    region: eastus
  - name: vm-rollback-test
    type: vm
    provider: azure
    region: eastus
"""

    first_upload = client.post(
        "/api/projects/demo-azure-core/templates/upload",
        files={"file": ("rollback-one.yaml", first_template, "text/yaml")},
        headers=auth_headers,
    )
    first_deployment = client.post(
        f"/api/templates/{first_upload.json()['template']['id']}/deploy",
        headers=auth_headers,
    ).json()

    second_upload = client.post(
        "/api/projects/demo-azure-core/templates/upload",
        files={"file": ("rollback-two.yaml", second_template, "text/yaml")},
        headers=auth_headers,
    )
    client.post(f"/api/templates/{second_upload.json()['template']['id']}/deploy", headers=auth_headers)

    rollback = client.post(
        f"/api/deployments/{first_deployment['id']}/rollback",
        json={"reason": "Return to storage baseline"},
        headers=auth_headers,
    )

    assert rollback.status_code == 201
    rollback_payload = rollback.json()
    assert rollback_payload["source_deployment_id"] == first_deployment["id"]
    assert rollback_payload["rollback_deployment"]["status"] == "success"
    assert rollback_payload["rollback_deployment"]["plan"]["summary"]["rollback"] == 2

    resources = client.get("/api/projects/demo-azure-core/resources", headers=auth_headers).json()
    resource_names = {resource["resource_name"] for resource in resources}

    assert resource_names == {"rg-rollback-test", "strollback001"}

    cost = client.get("/api/projects/demo-azure-core/cost-estimate", headers=auth_headers).json()

    assert cost["total_monthly_cost"] == 12


def test_plan_reports_drift_against_latest_deployment(client: TestClient, auth_headers: dict[str, str]) -> None:
    baseline_template = """
resources:
  - name: rg-drift-test
    type: resource_group
    provider: azure
    region: eastus
  - name: st-drift-test
    type: storage_account
    provider: azure
    region: eastus
"""
    drift_template = """
resources:
  - name: rg-drift-test
    type: resource_group
    provider: azure
    region: eastus
  - name: vm-drift-test
    type: vm
    provider: azure
    region: westus
"""

    baseline_upload = client.post(
        "/api/projects/demo-azure-core/templates/upload",
        files={"file": ("drift-baseline.yaml", baseline_template, "text/yaml")},
        headers=auth_headers,
    )
    client.post(f"/api/templates/{baseline_upload.json()['template']['id']}/deploy", headers=auth_headers)

    drift_upload = client.post(
        "/api/projects/demo-azure-core/templates/upload",
        files={"file": ("drift-next.yaml", drift_template, "text/yaml")},
        headers=auth_headers,
    )
    plan = client.post(f"/api/templates/{drift_upload.json()['template']['id']}/plan", headers=auth_headers)

    assert plan.status_code == 200
    payload = plan.json()
    assert payload["drift"]["creates"] == 1
    assert payload["drift"]["deletes"] == 1
    assert payload["drift"]["unchanged"] == 1
    assert payload["summary"]["create"] == 1
    assert payload["summary"]["delete"] == 1


def test_plan_reports_policy_violations(client: TestClient, auth_headers: dict[str, str]) -> None:
    template = """
resources:
  - name: public-ip-risk
    type: public_ip
    provider: azure
    region: eastus
  - name: vm-expensive-risk
    type: azurerm_windows_virtual_machine
    provider: azure
    region: eastus
"""

    upload = client.post(
        "/api/projects/demo-azure-core/templates/upload",
        files={"file": ("policy.yaml", template, "text/yaml")},
        headers=auth_headers,
    )
    plan = client.post(f"/api/templates/{upload.json()['template']['id']}/plan", headers=auth_headers)

    assert plan.status_code == 200
    rule_ids = {violation["rule_id"] for violation in plan.json()["policy_violations"]}
    assert "POLICY_PUBLIC_RESOURCE" in rule_ids
    assert "POLICY_EXPENSIVE_RESOURCE" in rule_ids


def test_deployments_are_isolated_by_environment(client: TestClient, auth_headers: dict[str, str]) -> None:
    stage_template = """
resources:
  - name: rg-stage-env
    type: resource_group
    provider: azure
    region: eastus
  - name: ststageenv001
    type: storage_account
    provider: azure
    region: eastus
    dependencies:
      - rg-stage-env
"""
    dev_template = """
resources:
  - name: rg-dev-env
    type: resource_group
    provider: azure
    region: eastus
"""

    stage_upload = client.post(
        "/api/projects/demo-azure-core/templates/upload",
        data={"environment": "stage"},
        files={"file": ("stage-env.yaml", stage_template, "text/yaml")},
        headers=auth_headers,
    )
    stage_template_id = stage_upload.json()["template"]["id"]
    stage_plan = client.post(f"/api/templates/{stage_template_id}/plan", headers=auth_headers).json()
    stage_deployment = client.post(f"/api/templates/{stage_template_id}/deploy", headers=auth_headers).json()

    assert stage_upload.status_code == 201
    assert stage_upload.json()["template"]["environment"] == "stage"
    assert stage_upload.json()["template"]["version"] == 1
    assert stage_plan["environment"] == "stage"
    assert stage_plan["summary"]["create"] == 2
    assert stage_deployment["environment"] == "stage"

    dev_resources = client.get(
        "/api/projects/demo-azure-core/resources?environment=dev",
        headers=auth_headers,
    ).json()
    stage_resources = client.get(
        "/api/projects/demo-azure-core/resources?environment=stage",
        headers=auth_headers,
    ).json()

    assert dev_resources == []
    assert {resource["resource_name"] for resource in stage_resources} == {"rg-stage-env", "ststageenv001"}
    assert all(resource["environment"] == "stage" for resource in stage_resources)

    dev_upload = client.post(
        "/api/projects/demo-azure-core/templates/upload",
        data={"environment": "dev"},
        files={"file": ("dev-env.yaml", dev_template, "text/yaml")},
        headers=auth_headers,
    )
    dev_deployment = client.post(f"/api/templates/{dev_upload.json()['template']['id']}/deploy", headers=auth_headers)
    stage_history = client.get(
        "/api/projects/demo-azure-core/deployments?environment=stage",
        headers=auth_headers,
    ).json()
    dev_cost = client.get(
        "/api/projects/demo-azure-core/cost-estimate?environment=dev",
        headers=auth_headers,
    ).json()
    stage_cost = client.get(
        "/api/projects/demo-azure-core/cost-estimate?environment=stage",
        headers=auth_headers,
    ).json()

    assert dev_upload.json()["template"]["version"] == 1
    assert dev_deployment.status_code == 201
    assert len(stage_history) == 1
    assert dev_cost["environment"] == "dev"
    assert dev_cost["total_monthly_cost"] == 0
    assert stage_cost["environment"] == "stage"
    assert stage_cost["total_monthly_cost"] == 12
