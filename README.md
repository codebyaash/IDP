# DeployForge

DeployForge is a Terraform Cloud-inspired infrastructure deployment platform for validating IaC templates, simulating deployment pipelines, visualizing resource graphs, estimating cloud costs, and managing rollback history.

The first portfolio version is intentionally simulation-first: it demonstrates DevOps, full-stack, and cloud engineering workflows without provisioning paid cloud resources.

## MVP Scope

- Email/password auth flow
- Project dashboard
- Terraform, YAML, JSON, and Bicep template upload
- IaC parsing and validation
- Deployment plan generation
- Mock deployment pipeline with logs
- Resource dependency graph
- Monthly cost estimate
- Deployment history
- Rollback to a previous successful version

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | Next.js, Tailwind CSS, React Flow, Recharts, lucide-react |
| Backend | FastAPI, Python, Pydantic |
| IaC Parsing | python-hcl2, PyYAML, JSON parser |
| Database | Supabase PostgreSQL |
| Hosting | Vercel Hobby, Render Free Web Service |
| CI/CD | GitHub Actions |

## Repository Structure

```text
DeployForge/
  frontend/          Next.js app
  backend/           FastAPI API and deployment simulator
  docs/              Architecture and planning notes
  sample-templates/  Demo IaC templates
```

## Local Development

Backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Portfolio Positioning

Built a Terraform Cloud-inspired infrastructure deployment platform that parses IaC templates, simulates deployment pipelines, visualizes cloud resource graphs, estimates infrastructure cost, and supports rollback workflows.
