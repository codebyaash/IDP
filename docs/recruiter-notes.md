# Recruiter Notes

## Project Summary

DeployForge is a Terraform Cloud-inspired infrastructure deployment platform. It parses IaC templates, simulates deployment pipelines, visualizes cloud resource graphs, estimates monthly cost, detects drift, runs policy checks, and supports rollback workflows.

## Resume Bullets

- Built a full-stack infrastructure deployment simulator using Next.js, FastAPI, SQLAlchemy, Alembic, and React Flow.
- Implemented IaC parsing for Terraform, YAML, JSON, and basic Bicep templates with deployment plan generation and policy checks.
- Designed environment-aware deployment state for `dev`, `stage`, and `prod`, including resource snapshots, cost estimates, history, and rollback.
- Created an interactive resource graph UX with dependency metrics, resource inspection, filtering, and deployment detail workflows.
- Added GitHub Actions CI for backend tests, migration smoke testing, dependency validation, frontend build, and TypeScript checks.

## Technical Talking Points

- Simulation-first architecture avoids real Azure costs while preserving platform engineering workflows.
- Resource snapshots make rollback deterministic and allow the graph/cost views to use deployed state instead of raw plans.
- Alembic migrations and database constraints harden the schema beyond a prototype.
- Swagger docs make the API easy to inspect and test during demos.
- The frontend is designed as an operational dashboard, not a marketing page.

## Suggested Portfolio Labels

```text
DevOps
Cloud Engineering
Platform Engineering
Full Stack
Infrastructure as Code
FastAPI
Next.js
React Flow
CI/CD
Alembic
```
