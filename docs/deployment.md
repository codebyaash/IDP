# Deployment Notes

DeployForge is designed for a free portfolio deployment with Vercel for the frontend and Render for the backend.

Current hosted demo:

```text
Frontend: https://deployforge-eight.vercel.app
Backend: https://deployforge-api.onrender.com
Swagger: https://deployforge-api.onrender.com/docs
```

## Backend

Use `render.yaml` as the Render blueprint.

Required production environment variables:

```text
APP_ENV=production
DATABASE_URL=<postgres-or-compatible-url>
SECRET_KEY=<long-random-secret>
CORS_ORIGINS=https://deployforge-eight.vercel.app
AUTO_CREATE_TABLES=false
REPAIR_LOCAL_SCHEMA=false
SEED_DEMO_DATA=false
```

The backend start command should run migrations before serving traffic:

```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Frontend

Set this environment variable in Vercel:

```text
NEXT_PUBLIC_API_BASE_URL=https://deployforge-api.onrender.com
```

Then deploy the `frontend` directory.

## Production Safety Checks

- `SECRET_KEY` cannot use the local development default when `APP_ENV=production`.
- `AUTO_CREATE_TABLES` must be `false` in production.
- `SEED_DEMO_DATA` must be `false` in production.
- `CORS_ORIGINS` should contain only the deployed frontend origin.
