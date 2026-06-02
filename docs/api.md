# DeployForge API

Initial API surface:

```text
GET    /health
POST   /api/auth/register
POST   /api/auth/login
GET    /api/projects
POST   /api/projects
GET    /api/projects/{project_id}
GET    /api/projects/{project_id}/templates
POST   /api/projects/{project_id}/templates/upload
GET    /api/projects/{project_id}/deployments
GET    /api/projects/{project_id}/resources
GET    /api/projects/{project_id}/cost-estimate
GET    /api/deployments/{deployment_id}
POST   /api/deployments/{deployment_id}/rollback
POST   /api/templates/validate
POST   /api/templates/plan
POST   /api/templates/{template_id}/plan
POST   /api/templates/{template_id}/deploy
POST   /api/templates/deploy
```

Project, template, deployment, resource, and cost endpoints require:

```text
Authorization: Bearer <access_token>
```

Planned API surface:

```text
GET    /projects/{id}/policy-checks
```
