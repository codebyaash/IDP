# DeployForge Architecture

DeployForge is a simulation-first infrastructure deployment platform. It is designed to look and behave like a cloud deployment control plane while avoiding real cloud provisioning costs.

## Request Flow

```text
User
  -> Next.js frontend
  -> FastAPI backend
  -> IaC parser and deployment simulator
  -> SQLite locally or Postgres-compatible DATABASE_URL
  -> deployment history, resource snapshots, resource graph, rollback history
```

## Core Backend Modules

- API routes accept uploaded Terraform, YAML, JSON, and Bicep templates.
- Parser services extract resource names, types, regions, dependencies, and cost hints.
- Planner services compare parsed templates with the latest simulated state for the selected environment.
- Deployment simulator emits deterministic pipeline steps and logs.
- Resource services persist deployment snapshots and power graph and cost endpoints.
- Rollback services restore resources from previous successful deployment snapshots.
- Project data is persisted with SQLAlchemy and managed with Alembic migrations.
- Runtime settings are controlled through environment variables for CORS, database URL, token secrets, demo seeding, and local schema repair.

## Database Tables

```text
users
projects
iac_templates
deployments
resources
rollback_events
```

Deployment steps, policy findings, drift summaries, and cost estimates are currently stored inside deployment plan JSON or derived from resource snapshots. This keeps the MVP compact while still preserving deployment history and rollback state.

## Environment Model

DeployForge stores independent simulated state for:

```text
dev
stage
prod
```

Template versioning, deployment history, latest resource snapshots, cost estimates, and resource graph data are all scoped by environment.

## Quality Gates

```text
GitHub Actions
  -> backend dependency check
  -> Alembic migration smoke test
  -> pytest
  -> frontend build
  -> frontend typecheck
```

## Free Hosting Plan

| Component | Platform |
| --- | --- |
| Frontend | Vercel Hobby |
| Backend | Render Free Web Service |
| Database | Supabase Free |
| CI/CD | GitHub Actions |

## Production Runtime

Production should use:

```text
APP_ENV=production
AUTO_CREATE_TABLES=false
REPAIR_LOCAL_SCHEMA=false
SEED_DEMO_DATA=false
```

Alembic migrations should run before API startup. The included `render.yaml` uses `alembic upgrade head` before launching `uvicorn`.
