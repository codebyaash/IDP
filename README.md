# DeployForge

DeployForge is a simulation-first infrastructure deployment platform inspired by Terraform Cloud and Azure Deployment Manager. It lets users upload IaC templates, validate and plan changes, simulate deployment pipelines, inspect resource graphs, estimate cost, and roll back previous deployment snapshots without provisioning real cloud resources.

This project is built as a portfolio-grade DevOps and full-stack system: it demonstrates cloud workflow design, API engineering, stateful deployment history, graph-based infrastructure UX, database migrations, and CI quality gates while staying safe to run for free.

## Recruiter Snapshot

**Portfolio pitch:** Built a Terraform Cloud-inspired deployment control plane that parses IaC, simulates environment-aware deployments, detects drift, runs policy checks, visualizes resource dependencies, estimates monthly cost, and supports rollback workflows.

**Best fit roles:** DevOps Engineer, Cloud Engineer, Platform Engineer, Full Stack Engineer.

**Project status:** Local demo ready. Hosted demo and screenshots are the next public-sharing items.

**What it proves:**

- Designed a full-stack deployment workflow from IaC upload to deployment history.
- Built a FastAPI backend with JWT auth, SQLAlchemy models, Alembic migrations, and Swagger docs.
- Implemented a Next.js operational dashboard with React Flow graphs, cost charts, environment filters, and deployment detail pages.
- Added CI checks for backend tests, frontend build/typecheck, dependency validation, and migration smoke testing.
- Kept the cloud workflow simulation-first to avoid accidental Azure spend while preserving enterprise-style behavior.

## Case Study

**Problem:** Real infrastructure deployment platforms are expensive or risky to demo because they can provision live cloud resources. A portfolio project still needs to show the same judgment recruiters care about: state management, deployment planning, policy checks, rollback safety, and operational UX.

**Solution:** DeployForge simulates the cloud control plane instead of the cloud provider. It parses templates into resources, compares desired state against the latest environment snapshot, produces a plan, runs a mock pipeline, persists deployment state, and exposes graph, cost, history, and rollback workflows.

**Impact:** The project demonstrates platform engineering depth without requiring Azure credentials, paid infrastructure, or a fragile demo environment.

## Feature Highlights

| Area | What DeployForge Does |
| --- | --- |
| Auth | Email/password auth with JWT-protected API routes |
| Projects | User-owned infrastructure workspaces |
| Environments | Independent `dev`, `stage`, and `prod` deployment state |
| IaC Upload | Supports Terraform, YAML, JSON, and basic Bicep parsing |
| Planning | Generates create/update/delete plans from parsed templates |
| Drift Detection | Compares new templates against latest simulated environment state |
| Policy Checks | Flags public resources, high-cost resources, and empty tag sets |
| Pipeline Simulation | Produces deterministic deployment steps and logs |
| Resource Graph | Interactive React Flow graph with filters, dependency metrics, and resource inspector |
| Cost Dashboard | Mock monthly cost estimates by resource type |
| History | Stores deployment records and resource snapshots |
| Rollback | Restores previous successful deployment snapshots |
| API Docs | Swagger UI at `/docs` |
| DB Hardening | Alembic migrations, constraints, indexes, and SQLite FK enforcement |
| CI | GitHub Actions for tests, migrations, frontend build, and typecheck |

## Architecture

```text
User
  -> Next.js dashboard
  -> FastAPI API
  -> IaC parser and deployment simulator
  -> SQLite locally or Postgres-compatible DATABASE_URL
  -> deployment history, resource snapshots, cost estimates, rollback events
```

The app does not deploy real Azure resources. Instead, it simulates the lifecycle a cloud platform team would care about:

```text
Upload IaC
  -> parse resources
  -> validate syntax
  -> compare against environment state
  -> generate plan and policy findings
  -> simulate pipeline stages
  -> persist resource snapshot
  -> visualize graph, cost, history, and rollback options
```

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | Next.js, TypeScript, Tailwind CSS, React Flow, Recharts, lucide-react |
| Backend | FastAPI, Python, Pydantic, SQLAlchemy |
| Auth | JWT with password hashing |
| IaC Parsing | python-hcl2, PyYAML, JSON parser, lightweight Bicep parser |
| Database | SQLite locally, Postgres-compatible via `DATABASE_URL` |
| Migrations | Alembic |
| CI/CD | GitHub Actions |
| Free Hosting Fit | Vercel Hobby frontend, Render backend, Supabase Postgres |

## Screens To Show

Add screenshots or a short GIF of these screens before sharing publicly:

- Dashboard with projects, pipeline, history, and cost chart
- Upload template and deployment plan with drift/policy findings
- Full resource graph with selected resource inspector
- Deployment detail page with logs, resource snapshot, and rollback action
- Swagger docs at `/docs`

## Demo Links

Local demo:

```text
Frontend: http://localhost:3001
Backend Swagger: http://127.0.0.1:8001/docs
```

Hosted demo:

```text
Coming soon
```

## Local Development

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8001
```

Local defaults are built in. Use `backend/.env.example` as the reference when setting shell or hosting environment variables. The backend seeds a demo user and project on startup unless `SEED_DEMO_DATA=false`.

```text
Email: ash@deployforge.local
Password: ashtest123
```

Useful backend URLs:

```text
API health: http://127.0.0.1:8001/health
Swagger UI: http://127.0.0.1:8001/docs
OpenAPI JSON: http://127.0.0.1:8001/openapi.json
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev -- -p 3001
```

Open:

```text
http://localhost:3001
```

## Quality Checks

Backend:

```bash
cd backend
python -m pip check
DATABASE_URL=sqlite:////tmp/deployforge_migration_smoke.db alembic upgrade head
pytest
```

Frontend:

```bash
cd frontend
npm run build
npm run typecheck
```

CI runs the same core checks in GitHub Actions:

- Backend dependency validation
- Alembic migration smoke test
- Pytest suite
- Frontend build
- Frontend TypeScript check

## Production Notes

Backend production deploys should run Alembic migrations before starting the API. The backend intentionally refuses unsafe production defaults, so these settings must be configured:

```text
APP_ENV=production
DATABASE_URL=<postgres-or-compatible-url>
SECRET_KEY=<long-random-secret>
CORS_ORIGINS=https://your-frontend-domain.example
AUTO_CREATE_TABLES=false
REPAIR_LOCAL_SCHEMA=false
SEED_DEMO_DATA=false
```

Render deployment starter config is included in `render.yaml`. For Vercel, set `NEXT_PUBLIC_API_BASE_URL` to the deployed backend URL.

## API Surface

Core authenticated endpoints:

```text
GET    /api/projects
POST   /api/projects
GET    /api/projects/{project_id}
GET    /api/projects/{project_id}/templates?environment=dev
POST   /api/projects/{project_id}/templates/upload
POST   /api/templates/{template_id}/plan
POST   /api/templates/{template_id}/deploy
GET    /api/projects/{project_id}/deployments?environment=dev
GET    /api/deployments/{deployment_id}
POST   /api/deployments/{deployment_id}/rollback
GET    /api/projects/{project_id}/resources?environment=dev
GET    /api/projects/{project_id}/cost-estimate?environment=dev
```

Auth endpoints:

```text
POST   /api/auth/register
POST   /api/auth/login
```

## Repository Structure

```text
DeployForge/
  backend/             FastAPI API, SQLAlchemy models, services, tests, Alembic migrations
  frontend/            Next.js app, dashboard, deployment detail route, API client
  docs/                Architecture, API notes, roadmap, demo script
  sample-templates/    Terraform and YAML templates for demos
  render.yaml           Render backend deployment blueprint
  .github/workflows/   CI pipeline
```

## Demo Flow

1. Sign in with the seeded demo credentials.
2. Upload `sample-templates/storage.yaml` into `dev`.
3. Review the deployment plan, drift summary, cost estimate, and policy findings.
4. Deploy the template and watch the pipeline/history update.
5. Open the resource graph and inspect dependencies.
6. Open a deployment detail page from history.
7. Upload a changed template in the same environment to show drift.
8. Roll back to a previous successful deployment.

## Roadmap

- Persist policy violations and audit logs as first-class tables.
- Add GitHub raw URL import for templates.
- Add screenshots and a hosted demo URL.
- Add Playwright coverage for dashboard and deployment detail workflows.
- Support richer Terraform expressions and Bicep resource dependency extraction.
