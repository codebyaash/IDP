# DeployForge API

Swagger UI is available at:

```text
GET /docs
```

OpenAPI JSON is available at:

```text
GET /openapi.json
```

Current API surface:

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

Environment-scoped endpoints accept:

```text
?environment=dev
?environment=stage
?environment=prod
```

Template upload accepts `environment` as a multipart form field.

## Demo Login

```text
Email: demo@deployforge.local
Password: deployforge123
```
