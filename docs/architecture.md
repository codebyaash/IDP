# DeployForge Architecture

DeployForge is a simulation-first infrastructure deployment platform. It is designed to look and behave like a cloud deployment control plane while avoiding real cloud provisioning costs.

## Request Flow

```text
User
  -> Next.js frontend
  -> FastAPI backend
  -> IaC parser and deployment simulator
  -> SQLite locally, Supabase PostgreSQL for hosted deployment
  -> resource graph, pipeline logs, rollback history
```

## Core Backend Modules

- API routes accept uploaded Terraform, YAML, JSON, and Bicep templates.
- Parser services extract resource names, types, regions, dependencies, and cost hints.
- Planner services compare parsed templates with simulated state.
- Deployment simulator emits deterministic pipeline steps and logs.
- Project data is persisted in a local SQLite database during development.
- History services will persist deployments, resources, rollback events, policy violations, and audit logs.

## Database Tables

```text
users
projects
iac_templates
deployments
deployment_steps
resources
rollback_events
cost_estimates
policy_violations
audit_logs
```

## Free Hosting Plan

| Component | Platform |
| --- | --- |
| Frontend | Vercel Hobby |
| Backend | Render Free Web Service |
| Database | Supabase Free |
| CI/CD | GitHub Actions |
