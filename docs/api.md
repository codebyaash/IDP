# DeployForge API

Initial API surface:

```text
GET    /health
GET    /api/projects
POST   /api/projects
GET    /api/projects/{project_id}
GET    /api/projects/{project_id}/templates
POST   /api/projects/{project_id}/templates/upload
GET    /api/projects/{project_id}/deployments
GET    /api/projects/{project_id}/resources
GET    /api/projects/{project_id}/cost-estimate
GET    /api/deployments/{deployment_id}
POST   /api/templates/validate
POST   /api/templates/plan
POST   /api/templates/{template_id}/plan
POST   /api/templates/{template_id}/deploy
POST   /api/templates/deploy
```

Planned API surface:

```text
POST   /auth/register
POST   /auth/login

GET    /projects
POST   /projects
GET    /projects/{id}

POST   /projects/{id}/templates/upload
GET    /projects/{id}/templates

POST   /templates/{id}/validate
POST   /templates/{id}/plan
POST   /templates/{id}/deploy

GET    /deployments/{id}
GET    /projects/{id}/deployments
POST   /deployments/{id}/rollback

GET    /projects/{id}/resources
GET    /projects/{id}/cost-estimate
GET    /projects/{id}/policy-checks
```
