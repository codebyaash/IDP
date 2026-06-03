# DeployForge Demo Script

Use this as a 2 to 4 minute walkthrough for a recruiter screen share or portfolio video.

## Opening

DeployForge is a simulation-first infrastructure deployment platform inspired by Terraform Cloud. It demonstrates the workflows a platform team would need: IaC upload, validation, planning, deployment simulation, drift detection, policy checks, cost estimates, resource graphing, deployment history, and rollback.

The app intentionally avoids provisioning real Azure resources, so it is safe to demo for free while still showing real engineering patterns.

## Walkthrough

1. Sign in with the seeded demo account.

```text
ash-prod@deploy-forge.local
ashprod123
```

2. Show the dashboard.

Point out projects, environment selection, recent deployment history, pipeline stages, cost dashboard, and CI-backed API quality.

3. Upload a sample template.

Use `sample-templates/storage.yaml` or `sample-templates/azure-network.tf`.

4. Review the deployment plan.

Call out create/update/delete actions, monthly cost, drift counters, and policy findings.

5. Run the simulated deployment.

Show the deterministic pipeline stages and logs. Explain that the simulator persists a resource snapshot for rollback and graph views.

6. Open the resource graph.

Show dependency edges, filters, selected resource inspector, dependencies, dependents, and metadata.

7. Open a deployment detail page.

Show pipeline logs, plan changes, resource snapshot, drift, policy findings, and rollback action.

8. Demonstrate environment isolation.

Switch from `dev` to `stage` or `prod` and explain that each environment has independent templates, history, resources, and cost state.

9. Close with the engineering story.

DeployForge combines full-stack product work with platform engineering concerns: auth, database design, migrations, CI, Swagger docs, graph UX, and deployment workflows.

## Interview Sound Bites

- "I built this simulation-first to show cloud deployment workflows without risking real cloud spend."
- "Deployments persist target resource snapshots, which makes rollback and graph views deterministic."
- "Drift detection compares a new template against the latest simulated state in the same environment."
- "The CI pipeline runs backend tests, a migration smoke test, frontend build, and TypeScript checks."
- "The graph is not just decorative; it exposes dependency health, unresolved references, dependents, and resource metadata."
