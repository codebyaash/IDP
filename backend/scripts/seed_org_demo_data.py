#!/usr/bin/env python3
"""Seed rich organization-scoped demo data for local DeployForge testing.

It is idempotent for records with the ``org-demo-`` prefix and keeps
manually-created user test data intact.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parents[1] / "deployforge.db"
ORG_ID = "deploy-forge.local"
ORG_NAME = "Deploy Forge"
SEED_USER_ID = "ash-prod-deploy-forge-local"
SEED_USER_EMAIL = "ash-prod@deploy-forge.local"
SEED_USER_PASSWORD = "ashprod123"
NOW = datetime(2026, 6, 3, 10, 0, 0)
ACTIVE_SEED_USER_ID = SEED_USER_ID

FALLBACK_PASSWORD_HASH = "$2b$12$eXFM8lGf6s6oB3DFoBszGeg6HvogtkKSjo2Qs2fF3caTAzT/3ddN."


PROJECTS = [
    {
        "id": "org-demo-platform-core",
        "name": "DeployForge Platform Core",
        "environment": "dev",
        "monthly_cost": 536,
        "envs": {
            "dev": [
                ("rg-df-dev-core", "resource_group", "eastus", [], 0, {"tier": "foundation"}),
                ("vnet-df-dev-core", "virtual_network", "eastus", ["rg-df-dev-core"], 35, {"cidr": "10.10.0.0/16"}),
                ("subnet-df-dev-api", "subnet", "eastus", ["vnet-df-dev-core"], 10, {"cidr": "10.10.1.0/24"}),
                ("stdfdevstate001", "storage_account", "eastus", ["rg-df-dev-core"], 12, {"replication": "LRS"}),
                ("kv-df-dev-core", "key_vault", "eastus", ["rg-df-dev-core"], 18, {"soft_delete": True}),
                ("app-df-dev-api", "app_service", "eastus", ["subnet-df-dev-api", "kv-df-dev-core"], 62, {"sku": "B1"}),
            ],
            "stage": [
                ("rg-df-stage-core", "resource_group", "eastus2", [], 0, {"tier": "foundation"}),
                ("vnet-df-stage-core", "virtual_network", "eastus2", ["rg-df-stage-core"], 48, {"cidr": "10.20.0.0/16"}),
                ("subnet-df-stage-api", "subnet", "eastus2", ["vnet-df-stage-core"], 14, {"cidr": "10.20.1.0/24"}),
                ("stdfstagestate001", "storage_account", "eastus2", ["rg-df-stage-core"], 24, {"replication": "ZRS"}),
                ("kv-df-stage-core", "key_vault", "eastus2", ["rg-df-stage-core"], 24, {"soft_delete": True}),
                ("app-df-stage-api", "app_service", "eastus2", ["subnet-df-stage-api", "kv-df-stage-core"], 96, {"sku": "S1"}),
                ("appi-df-stage", "application_insights", "eastus2", ["app-df-stage-api"], 22, {"retention_days": 30}),
            ],
            "prod": [
                ("rg-df-prod-core", "resource_group", "centralus", [], 0, {"tier": "foundation"}),
                ("vnet-df-prod-core", "virtual_network", "centralus", ["rg-df-prod-core"], 72, {"cidr": "10.30.0.0/16"}),
                ("subnet-df-prod-api", "subnet", "centralus", ["vnet-df-prod-core"], 18, {"cidr": "10.30.1.0/24"}),
                ("stdfprodstate001", "storage_account", "centralus", ["rg-df-prod-core"], 48, {"replication": "GRS"}),
                ("kv-df-prod-core", "key_vault", "centralus", ["rg-df-prod-core"], 36, {"soft_delete": True}),
                ("app-df-prod-api", "app_service", "centralus", ["subnet-df-prod-api", "kv-df-prod-core"], 184, {"sku": "P1v3"}),
                ("appi-df-prod", "application_insights", "centralus", ["app-df-prod-api"], 42, {"retention_days": 90}),
                ("agw-df-prod", "application_gateway", "centralus", ["subnet-df-prod-api"], 136, {"waf": True}),
            ],
        },
    },
    {
        "id": "org-demo-payments-edge",
        "name": "Payments Edge Services",
        "environment": "stage",
        "monthly_cost": 708,
        "envs": {
            "dev": [
                ("rg-pay-dev", "resource_group", "westus", [], 0, {"owner": "payments"}),
                ("vnet-pay-dev", "virtual_network", "westus", ["rg-pay-dev"], 32, {"cidr": "10.40.0.0/16"}),
                ("stpaydevledger001", "storage_account", "westus", ["rg-pay-dev"], 12, {"replication": "LRS"}),
                ("sql-pay-dev", "sql_database", "westus", ["rg-pay-dev"], 78, {"tier": "Basic"}),
                ("func-pay-dev", "function_app", "westus", ["stpaydevledger001", "sql-pay-dev"], 44, {"runtime": "python"}),
            ],
            "stage": [
                ("rg-pay-stage", "resource_group", "westus2", [], 0, {"owner": "payments"}),
                ("vnet-pay-stage", "virtual_network", "westus2", ["rg-pay-stage"], 48, {"cidr": "10.50.0.0/16"}),
                ("stpaystageledger001", "storage_account", "westus2", ["rg-pay-stage"], 24, {"replication": "ZRS"}),
                ("sql-pay-stage", "sql_database", "westus2", ["rg-pay-stage"], 156, {"tier": "Standard"}),
                ("func-pay-stage", "function_app", "westus2", ["stpaystageledger001", "sql-pay-stage"], 92, {"runtime": "python"}),
                ("sb-pay-stage", "service_bus_namespace", "westus2", ["func-pay-stage"], 38, {"sku": "Standard"}),
            ],
            "prod": [
                ("rg-pay-prod", "resource_group", "eastus", [], 0, {"owner": "payments"}),
                ("vnet-pay-prod", "virtual_network", "eastus", ["rg-pay-prod"], 88, {"cidr": "10.60.0.0/16"}),
                ("stpayprodledger001", "storage_account", "eastus", ["rg-pay-prod"], 58, {"replication": "GRS"}),
                ("sql-pay-prod", "sql_database", "eastus", ["rg-pay-prod"], 312, {"tier": "Premium"}),
                ("func-pay-prod", "function_app", "eastus", ["stpayprodledger001", "sql-pay-prod"], 148, {"runtime": "python"}),
                ("sb-pay-prod", "service_bus_namespace", "eastus", ["func-pay-prod"], 64, {"sku": "Premium"}),
                ("pip-pay-prod", "public_ip", "eastus", ["rg-pay-prod"], 38, {"exposure": "internet-facing"}),
            ],
        },
    },
    {
        "id": "org-demo-analytics",
        "name": "Analytics Landing Zone",
        "environment": "prod",
        "monthly_cost": 925,
        "envs": {
            "dev": [
                ("rg-ana-dev", "resource_group", "southcentralus", [], 0, {"owner": "data"}),
                ("st-anadev-raw", "storage_account", "southcentralus", ["rg-ana-dev"], 18, {"container": "raw"}),
                ("st-anadev-curated", "storage_account", "southcentralus", ["rg-ana-dev"], 18, {"container": "curated"}),
                ("syn-ana-dev", "synapse_workspace", "southcentralus", ["st-anadev-raw", "st-anadev-curated"], 126, {"spark_pool": "small"}),
            ],
            "stage": [
                ("rg-ana-stage", "resource_group", "southcentralus", [], 0, {"owner": "data"}),
                ("vnet-ana-stage", "virtual_network", "southcentralus", ["rg-ana-stage"], 46, {"cidr": "10.70.0.0/16"}),
                ("st-anastage-raw", "storage_account", "southcentralus", ["rg-ana-stage"], 32, {"container": "raw"}),
                ("st-anastage-curated", "storage_account", "southcentralus", ["rg-ana-stage"], 32, {"container": "curated"}),
                ("syn-ana-stage", "synapse_workspace", "southcentralus", ["vnet-ana-stage", "st-anastage-raw", "st-anastage-curated"], 228, {"spark_pool": "medium"}),
            ],
            "prod": [
                ("rg-ana-prod", "resource_group", "northcentralus", [], 0, {"owner": "data"}),
                ("vnet-ana-prod", "virtual_network", "northcentralus", ["rg-ana-prod"], 82, {"cidr": "10.80.0.0/16"}),
                ("st-anaprod-raw", "storage_account", "northcentralus", ["rg-ana-prod"], 74, {"container": "raw", "replication": "GRS"}),
                ("st-anaprod-curated", "storage_account", "northcentralus", ["rg-ana-prod"], 74, {"container": "curated", "replication": "GRS"}),
                ("syn-ana-prod", "synapse_workspace", "northcentralus", ["vnet-ana-prod", "st-anaprod-raw", "st-anaprod-curated"], 418, {"spark_pool": "large"}),
                ("kv-ana-prod", "key_vault", "northcentralus", ["rg-ana-prod"], 32, {"soft_delete": True}),
                ("vm-ana-prod-jumpbox", "azurerm_linux_virtual_machine", "northcentralus", ["vnet-ana-prod", "kv-ana-prod"], 245, {"size": "Standard_D8s_v5"}),
            ],
        },
    },
    {
        "id": "org-demo-prod-reliability",
        "name": "Production Reliability Command Center",
        "environment": "prod",
        "monthly_cost": 1188,
        "envs": {
            "dev": [
                ("rg-rel-dev", "resource_group", "eastus", [], 0, {"owner": "sre"}),
                ("vnet-rel-dev", "virtual_network", "eastus", ["rg-rel-dev"], 36, {"cidr": "10.90.0.0/16"}),
                ("log-rel-dev", "log_analytics_workspace", "eastus", ["rg-rel-dev"], 44, {"retention_days": 30}),
                ("appi-rel-dev", "application_insights", "eastus", ["log-rel-dev"], 26, {"sampling": "adaptive"}),
                ("func-rel-dev-alerts", "function_app", "eastus", ["appi-rel-dev"], 52, {"runtime": "python"}),
            ],
            "stage": [
                ("rg-rel-stage", "resource_group", "eastus2", [], 0, {"owner": "sre"}),
                ("vnet-rel-stage", "virtual_network", "eastus2", ["rg-rel-stage"], 54, {"cidr": "10.91.0.0/16"}),
                ("log-rel-stage", "log_analytics_workspace", "eastus2", ["rg-rel-stage"], 92, {"retention_days": 60}),
                ("appi-rel-stage", "application_insights", "eastus2", ["log-rel-stage"], 48, {"sampling": "adaptive"}),
                ("func-rel-stage-alerts", "function_app", "eastus2", ["appi-rel-stage"], 88, {"runtime": "python"}),
                ("sb-rel-stage", "service_bus_namespace", "eastus2", ["func-rel-stage-alerts"], 42, {"sku": "Standard"}),
            ],
            "prod": [
                ("rg-rel-prod", "resource_group", "centralus", [], 0, {"owner": "sre"}),
                ("vnet-rel-prod", "virtual_network", "centralus", ["rg-rel-prod"], 96, {"cidr": "10.92.0.0/16"}),
                ("log-rel-prod", "log_analytics_workspace", "centralus", ["rg-rel-prod"], 226, {"retention_days": 180}),
                ("appi-rel-prod", "application_insights", "centralus", ["log-rel-prod"], 86, {"sampling": "adaptive"}),
                ("func-rel-prod-alerts", "function_app", "centralus", ["appi-rel-prod"], 144, {"runtime": "python"}),
                ("sb-rel-prod", "service_bus_namespace", "centralus", ["func-rel-prod-alerts"], 74, {"sku": "Premium"}),
                ("agw-rel-prod", "application_gateway", "centralus", ["vnet-rel-prod"], 168, {"waf": True}),
                ("pip-rel-prod-status", "public_ip", "centralus", ["agw-rel-prod"], 38, {"exposure": "status-page"}),
            ],
        },
    },
    {
        "id": "org-demo-prod-identity",
        "name": "Zero Trust Identity Plane",
        "environment": "prod",
        "monthly_cost": 842,
        "envs": {
            "dev": [
                ("rg-id-dev", "resource_group", "westus2", [], 0, {"owner": "security"}),
                ("kv-id-dev", "key_vault", "westus2", ["rg-id-dev"], 22, {"soft_delete": True}),
                ("st-id-dev-audit", "storage_account", "westus2", ["rg-id-dev"], 14, {"container": "audit"}),
                ("func-id-dev-claims", "function_app", "westus2", ["kv-id-dev", "st-id-dev-audit"], 48, {"runtime": "node"}),
            ],
            "stage": [
                ("rg-id-stage", "resource_group", "westus2", [], 0, {"owner": "security"}),
                ("vnet-id-stage", "virtual_network", "westus2", ["rg-id-stage"], 52, {"cidr": "10.100.0.0/16"}),
                ("kv-id-stage", "key_vault", "westus2", ["rg-id-stage"], 34, {"soft_delete": True}),
                ("st-id-stage-audit", "storage_account", "westus2", ["rg-id-stage"], 32, {"container": "audit"}),
                ("func-id-stage-claims", "function_app", "westus2", ["kv-id-stage", "st-id-stage-audit"], 96, {"runtime": "node"}),
                ("sql-id-stage", "sql_database", "westus2", ["rg-id-stage"], 142, {"tier": "Standard"}),
            ],
            "prod": [
                ("rg-id-prod", "resource_group", "eastus", [], 0, {"owner": "security"}),
                ("vnet-id-prod", "virtual_network", "eastus", ["rg-id-prod"], 88, {"cidr": "10.101.0.0/16"}),
                ("kv-id-prod", "key_vault", "eastus", ["rg-id-prod"], 48, {"soft_delete": True}),
                ("st-id-prod-audit", "storage_account", "eastus", ["rg-id-prod"], 64, {"container": "audit", "replication": "GRS"}),
                ("func-id-prod-claims", "function_app", "eastus", ["kv-id-prod", "st-id-prod-audit"], 148, {"runtime": "node"}),
                ("sql-id-prod", "sql_database", "eastus", ["rg-id-prod"], 288, {"tier": "Premium"}),
                ("vm-id-prod-breakglass", "azurerm_windows_virtual_machine", "eastus", ["vnet-id-prod", "kv-id-prod"], 232, {"size": "Standard_D8s_v5"}),
            ],
        },
    },
    {
        "id": "org-demo-prod-commerce",
        "name": "Multi Region Commerce Platform",
        "environment": "prod",
        "monthly_cost": 1476,
        "envs": {
            "dev": [
                ("rg-com-dev", "resource_group", "centralus", [], 0, {"owner": "commerce"}),
                ("vnet-com-dev", "virtual_network", "centralus", ["rg-com-dev"], 44, {"cidr": "10.110.0.0/16"}),
                ("st-com-dev-catalog", "storage_account", "centralus", ["rg-com-dev"], 18, {"container": "catalog"}),
                ("sql-com-dev", "sql_database", "centralus", ["rg-com-dev"], 84, {"tier": "Basic"}),
                ("app-com-dev-api", "app_service", "centralus", ["vnet-com-dev", "sql-com-dev"], 66, {"sku": "B1"}),
            ],
            "stage": [
                ("rg-com-stage", "resource_group", "centralus", [], 0, {"owner": "commerce"}),
                ("vnet-com-stage", "virtual_network", "centralus", ["rg-com-stage"], 68, {"cidr": "10.111.0.0/16"}),
                ("st-com-stage-catalog", "storage_account", "centralus", ["rg-com-stage"], 38, {"container": "catalog"}),
                ("sql-com-stage", "sql_database", "centralus", ["rg-com-stage"], 176, {"tier": "Standard"}),
                ("app-com-stage-api", "app_service", "centralus", ["vnet-com-stage", "sql-com-stage"], 118, {"sku": "S1"}),
                ("cdn-com-stage", "cdn_profile", "centralus", ["st-com-stage-catalog"], 46, {"sku": "Standard"}),
            ],
            "prod": [
                ("rg-com-prod-primary", "resource_group", "eastus", [], 0, {"owner": "commerce"}),
                ("rg-com-prod-secondary", "resource_group", "westus2", [], 0, {"owner": "commerce"}),
                ("vnet-com-prod-primary", "virtual_network", "eastus", ["rg-com-prod-primary"], 96, {"cidr": "10.112.0.0/16"}),
                ("vnet-com-prod-secondary", "virtual_network", "westus2", ["rg-com-prod-secondary"], 96, {"cidr": "10.113.0.0/16"}),
                ("st-com-prod-catalog", "storage_account", "eastus", ["rg-com-prod-primary"], 82, {"container": "catalog", "replication": "GRS"}),
                ("sql-com-prod", "sql_database", "eastus", ["rg-com-prod-primary"], 356, {"tier": "BusinessCritical"}),
                ("app-com-prod-api", "app_service", "eastus", ["vnet-com-prod-primary", "sql-com-prod"], 214, {"sku": "P1v3"}),
                ("app-com-prod-dr", "app_service", "westus2", ["vnet-com-prod-secondary", "sql-com-prod"], 176, {"sku": "P1v3"}),
                ("cdn-com-prod", "cdn_profile", "eastus", ["st-com-prod-catalog"], 74, {"sku": "Premium"}),
                ("pip-com-prod", "public_ip", "eastus", ["app-com-prod-api"], 38, {"exposure": "checkout"}),
            ],
        },
    },
]


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"Database not found: {DB_PATH}")

    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    ensure_schema(con)
    seed_user(con)
    clear_previous_seed(con)
    seed_projects(con)
    con.commit()
    print_summary(con)
    con.close()


def ensure_schema(con: sqlite3.Connection) -> None:
    if not has_column(con, "users", "organization_id"):
        con.execute("ALTER TABLE users ADD COLUMN organization_id VARCHAR DEFAULT 'deployforge.local' NOT NULL")
    if not has_column(con, "users", "organization_name"):
        con.execute("ALTER TABLE users ADD COLUMN organization_name VARCHAR DEFAULT 'Deployforge' NOT NULL")
    if not has_column(con, "projects", "organization_id"):
        con.execute("ALTER TABLE projects ADD COLUMN organization_id VARCHAR DEFAULT 'deployforge.local' NOT NULL")
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_logs (
          id VARCHAR PRIMARY KEY,
          user_id VARCHAR NOT NULL,
          organization_id VARCHAR NOT NULL,
          action VARCHAR(80) NOT NULL,
          entity_type VARCHAR(80) NOT NULL,
          entity_id VARCHAR(255),
          project_id VARCHAR,
          environment VARCHAR(40),
          message VARCHAR(500) NOT NULL,
          metadata_json JSON NOT NULL,
          created_at DATETIME NOT NULL,
          FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    con.execute("CREATE INDEX IF NOT EXISTS ix_users_organization_id ON users (organization_id)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_projects_organization_created_at ON projects (organization_id, created_at)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_user_created_at ON audit_logs (user_id, created_at)")
    con.execute(
        "CREATE INDEX IF NOT EXISTS ix_audit_logs_organization_created_at ON audit_logs (organization_id, created_at)"
    )
    con.execute(
        """
        UPDATE projects
        SET organization_id = COALESCE((SELECT users.organization_id FROM users WHERE users.id = projects.user_id), organization_id)
        WHERE organization_id IS NULL OR organization_id = ''
        """
    )


def has_column(con: sqlite3.Connection, table: str, column: str) -> bool:
    return any(row[1] == column for row in con.execute(f"PRAGMA table_info({table})"))


def seed_user(con: sqlite3.Connection) -> None:
    global ACTIVE_SEED_USER_ID

    existing = con.execute("SELECT id FROM users WHERE id = ?", (SEED_USER_ID,)).fetchone()
    existing_by_email = con.execute("SELECT id FROM users WHERE email = ?", (SEED_USER_EMAIL,)).fetchone()
    password_hash = hash_seed_password()
    if existing_by_email:
        ACTIVE_SEED_USER_ID = existing_by_email[0]
        con.execute(
            "UPDATE users SET organization_id = ?, organization_name = ?, password_hash = ? WHERE id = ?",
            (ORG_ID, ORG_NAME, password_hash, ACTIVE_SEED_USER_ID),
        )
        return
    if existing:
        ACTIVE_SEED_USER_ID = existing[0]
        con.execute(
            "UPDATE users SET email = ?, organization_id = ?, organization_name = ?, password_hash = ? WHERE id = ?",
            (SEED_USER_EMAIL, ORG_ID, ORG_NAME, password_hash, ACTIVE_SEED_USER_ID),
        )
        return

    con.execute(
        """
        INSERT INTO users (id, email, organization_id, organization_name, password_hash, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (SEED_USER_ID, SEED_USER_EMAIL, ORG_ID, ORG_NAME, password_hash, timestamp(0)),
    )


def hash_seed_password() -> str:
    try:
        from passlib.context import CryptContext

        return CryptContext(schemes=["bcrypt"], deprecated="auto").hash(SEED_USER_PASSWORD)
    except Exception:
        return FALLBACK_PASSWORD_HASH


def clear_previous_seed(con: sqlite3.Connection) -> None:
    project_ids = [project["id"] for project in PROJECTS]
    placeholders = ",".join("?" for _ in project_ids)
    con.execute(f"DELETE FROM resources WHERE project_id IN ({placeholders})", project_ids)
    con.execute(f"DELETE FROM rollback_events WHERE project_id IN ({placeholders})", project_ids)
    con.execute(f"DELETE FROM deployments WHERE project_id IN ({placeholders})", project_ids)
    con.execute(f"DELETE FROM iac_templates WHERE project_id IN ({placeholders})", project_ids)
    con.execute(f"DELETE FROM audit_logs WHERE project_id IN ({placeholders}) OR id LIKE 'org-demo-%'", project_ids)
    con.execute(f"DELETE FROM projects WHERE id IN ({placeholders})", project_ids)


def seed_projects(con: sqlite3.Connection) -> None:
    offset = 1
    for project in PROJECTS:
        con.execute(
            """
            INSERT INTO projects
              (id, user_id, organization_id, name, cloud_provider, environment, status, monthly_cost, created_at)
            VALUES (?, ?, ?, ?, 'azure', ?, 'deployed', ?, ?)
            """,
            (
                project["id"],
                ACTIVE_SEED_USER_ID,
                ORG_ID,
                project["name"],
                project["environment"],
                project["monthly_cost"],
                timestamp(offset),
            ),
        )
        add_audit(
            con,
            f"org-demo-audit-project-{project['id']}",
            "created_project",
            "project",
            project["id"],
            project["id"],
            project["environment"],
            f"Created seeded project {project['name']}.",
            {"seeded": True},
            offset,
        )
        offset += 1

        for env, resources in project["envs"].items():
            template_id = f"org-demo-template-{project['id']}-{env}"
            deployment_id = f"org-demo-deployment-{project['id']}-{env}"
            resource_payloads = [resource_payload(item) for item in resources]
            total_cost = sum(resource["estimated_monthly_cost"] for resource in resource_payloads)
            file_name = f"{project['id']}-{env}.yaml"
            plan = deployment_plan(file_name, env, resource_payloads)
            steps = deployment_steps(project["name"], env, len(resource_payloads), total_cost)

            con.execute(
                """
                INSERT INTO iac_templates
                  (id, project_id, environment, file_name, file_type, raw_content, parsed_json, version, created_at)
                VALUES (?, ?, ?, ?, 'yaml', ?, ?, 1, ?)
                """,
                (
                    template_id,
                    project["id"],
                    env,
                    file_name,
                    raw_content(project["name"], env, resource_payloads),
                    json.dumps({"file_name": file_name, "file_type": "yaml", "resources": resource_payloads}),
                    timestamp(offset),
                ),
            )
            add_audit(
                con,
                f"org-demo-audit-template-{project['id']}-{env}",
                "uploaded_template",
                "template",
                template_id,
                project["id"],
                env,
                f"Uploaded seeded {env} template for {project['name']}.",
                {"resource_count": len(resource_payloads), "version": 1},
                offset,
            )
            offset += 1

            con.execute(
                """
                INSERT INTO deployments
                  (id, project_id, environment, status, template_name, plan_json, estimated_monthly_cost, created_at)
                VALUES (?, ?, ?, 'success', ?, ?, ?, ?)
                """,
                (
                    deployment_id,
                    project["id"],
                    env,
                    file_name,
                    json.dumps({"template_id": template_id, "template_version": 1, "plan": plan, "steps": steps}),
                    total_cost,
                    timestamp(offset),
                ),
            )
            add_audit(
                con,
                f"org-demo-audit-deployment-{project['id']}-{env}",
                "deployed_template",
                "deployment",
                deployment_id,
                project["id"],
                env,
                f"Ran seeded {env} deployment for {project['name']}.",
                {"template_id": template_id, "monthly_cost": total_cost},
                offset,
            )
            offset += 1

            for index, resource in enumerate(resource_payloads, start=1):
                con.execute(
                    """
                    INSERT INTO resources
                      (id, project_id, deployment_id, environment, resource_name, resource_type, provider, region,
                       dependencies, estimated_monthly_cost, resource_metadata, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f"org-demo-resource-{project['id']}-{env}-{index}",
                        project["id"],
                        deployment_id,
                        env,
                        resource["name"],
                        resource["type"],
                        resource["provider"],
                        resource["region"],
                        json.dumps(resource["dependencies"]),
                        resource["estimated_monthly_cost"],
                        json.dumps(resource["metadata"]),
                        timestamp(offset),
                    ),
                )
            offset += 1


def resource_payload(item: tuple[str, str, str, list[str], float, dict[str, Any]]) -> dict[str, Any]:
    name, resource_type, region, dependencies, monthly_cost, metadata = item
    return {
        "name": name,
        "type": resource_type,
        "provider": "azure",
        "region": region,
        "dependencies": dependencies,
        "estimated_monthly_cost": monthly_cost,
        "metadata": metadata,
    }


def deployment_plan(file_name: str, env: str, resources: list[dict[str, Any]]) -> dict[str, Any]:
    policy_violations = []
    for resource in resources:
        if resource["type"] == "public_ip":
            policy_violations.append(
                {
                    "rule_id": "POLICY_PUBLIC_RESOURCE",
                    "severity": "high",
                    "resource_name": resource["name"],
                    "resource_type": resource["type"],
                    "message": "Public IP requires explicit production approval.",
                }
            )
        if "virtual_machine" in resource["type"] and resource["estimated_monthly_cost"] >= 200:
            policy_violations.append(
                {
                    "rule_id": "POLICY_EXPENSIVE_RESOURCE",
                    "severity": "medium",
                    "resource_name": resource["name"],
                    "resource_type": resource["type"],
                    "message": "Large VM size should be reviewed before deployment.",
                }
            )

    return {
        "template_name": file_name,
        "environment": env,
        "summary": {"create": len(resources), "update": 0, "delete": 0},
        "changes": [
            {"action": "create", "resource": resource, "reason": "Seeded baseline resource for organization testing."}
            for resource in resources
        ],
        "estimated_monthly_cost": sum(resource["estimated_monthly_cost"] for resource in resources),
        "target_resources": resources,
        "drift": {"creates": len(resources), "updates": 0, "deletes": 0, "unchanged": 0},
        "policy_violations": policy_violations,
    }


def deployment_steps(project_name: str, env: str, resource_count: int, monthly_cost: float) -> list[dict[str, Any]]:
    return [
        {
            "name": "Queued",
            "status": "success",
            "logs": [f"{project_name} {env} deployment queued for simulation."],
            "sequence_order": 1,
        },
        {
            "name": "Validating",
            "status": "success",
            "logs": [f"{resource_count} resources parsed and validated."],
            "sequence_order": 2,
        },
        {
            "name": "Planning",
            "status": "success",
            "logs": [f"Plan generated with estimated monthly cost ${monthly_cost}."],
            "sequence_order": 3,
        },
        {
            "name": "Deploying",
            "status": "success",
            "logs": ["Mock Azure deployment stages completed without provisioning real infrastructure."],
            "sequence_order": 4,
        },
        {
            "name": "Success",
            "status": "success",
            "logs": ["Resource snapshot, cost estimate, and deployment history persisted."],
            "sequence_order": 5,
        },
    ]


def raw_content(project_name: str, env: str, resources: list[dict[str, Any]]) -> str:
    lines = [f"name: {project_name}", f"environment: {env}", "resources:"]
    for resource in resources:
        lines.extend(
            [
                f"  - name: {resource['name']}",
                f"    type: {resource['type']}",
                f"    provider: {resource['provider']}",
                f"    region: {resource['region']}",
                f"    estimated_monthly_cost: {resource['estimated_monthly_cost']}",
            ]
        )
        if resource["dependencies"]:
            lines.append("    dependencies:")
            lines.extend(f"      - {dependency}" for dependency in resource["dependencies"])
    return "\n".join(lines) + "\n"


def add_audit(
    con: sqlite3.Connection,
    audit_id: str,
    action: str,
    entity_type: str,
    entity_id: str,
    project_id: str,
    environment: str,
    message: str,
    metadata: dict[str, Any],
    offset: int,
) -> None:
    con.execute(
        """
        INSERT INTO audit_logs
          (id, user_id, organization_id, action, entity_type, entity_id, project_id, environment, message, metadata_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            audit_id,
            ACTIVE_SEED_USER_ID,
            ORG_ID,
            action,
            entity_type,
            entity_id,
            project_id,
            environment,
            message,
            json.dumps(metadata),
            timestamp(offset),
        ),
    )


def timestamp(offset_minutes: int) -> str:
    return (NOW + timedelta(minutes=offset_minutes)).isoformat(sep=" ")


def print_summary(con: sqlite3.Connection) -> None:
    project_count = con.execute("SELECT COUNT(*) FROM projects WHERE organization_id = ?", (ORG_ID,)).fetchone()[0]
    deployment_count = con.execute(
        """
        SELECT COUNT(*)
        FROM deployments
        JOIN projects ON projects.id = deployments.project_id
        WHERE projects.organization_id = ?
        """,
        (ORG_ID,),
    ).fetchone()[0]
    resource_count = con.execute(
        """
        SELECT COUNT(*)
        FROM resources
        JOIN projects ON projects.id = resources.project_id
        WHERE projects.organization_id = ?
        """,
        (ORG_ID,),
    ).fetchone()[0]
    print(f"Seeded account: {SEED_USER_EMAIL} / {SEED_USER_PASSWORD}")
    print(f"Seeded organization: {ORG_ID}")
    print(f"Projects visible to {ORG_ID}: {project_count}")
    print(f"Deployments visible to {ORG_ID}: {deployment_count}")
    print(f"Resources visible to {ORG_ID}: {resource_count}")
    print(f"Create users like alice@{ORG_ID} to verify shared organization data.")


if __name__ == "__main__":
    main()
