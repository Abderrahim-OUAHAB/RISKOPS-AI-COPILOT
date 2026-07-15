# Deployment Guide

AI RiskOps Copilot is currently packaged for a local Docker Compose deployment. This guide documents the clean deployment path, required variables, health checks and production limits.

## Local Docker Compose

Start the lightweight interactive application without Airflow:

```powershell
docker compose up -d --build postgres backend frontend
```

Start the full local stack, including Airflow:

```powershell
docker compose up -d --build
```

Validate the stack:

```powershell
docker compose ps
curl http://localhost:8000/health
curl http://localhost:8000/ready
curl http://localhost:8501/
```

Open Streamlit at `http://localhost:8501`, and stop all local services with:

```powershell
docker compose down
```

Main ports:

- `8000`: FastAPI backend and Swagger docs at `/docs`
- `8501`: Streamlit frontend
- `5432`: PostgreSQL with pgvector
- `8080`: Airflow webserver

## Environment Variables

Use `.env.example` for local development and `.env.production.example` as the production checklist. Never commit a real `.env`.

Important variables:

- `DATABASE_URL`: SQLAlchemy database URL used by FastAPI.
- `OPENAI_API_KEY`: optional for RAG embeddings and generated answers.
- `OPENAI_TIMEOUT_SECONDS`: timeout applied to OpenAI SDK requests.
- `OPENAI_MAX_RETRIES`: bounded retries handled by the OpenAI SDK.
- `OPENAI_MAX_OUTPUT_TOKENS`: output limit for generated RAG answers.
- `BACKEND_CORS_ORIGINS`: comma-separated allowed frontend origins.
- `MAX_UPLOAD_SIZE_MB`: upload size limit.
- `RATE_LIMIT_PER_MINUTE`: simple per-IP rate limit.
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`: database bootstrap values.

## Health Checks

FastAPI exposes:

- `/health`: service, database, model and pgvector status.
- `/ready`: readiness checks for database connectivity, tables, model artifact and monitoring folders.

Docker Compose also defines container health checks for backend, frontend, PostgreSQL and Airflow webserver.

## Simple VPS Deployment

For a small VPS demo:

1. Install Docker and Docker Compose.
2. Clone the repository.
3. Create a real `.env` from `.env.production.example`.
4. Set strong database credentials and narrow CORS origins.
5. Run `docker compose up -d --build`.
6. Put a reverse proxy such as Nginx or Caddy in front of FastAPI and Streamlit.
7. Use HTTPS and restrict access to Airflow.
8. Back up the PostgreSQL volume.

This is acceptable for a controlled portfolio demo, not for enterprise production.

## CI/CD

The CI workflow validates Python compilation, minimal imports, Docker Compose configuration, required docs and tracked-file hygiene.

Install and run the focused local test suite with:

```powershell
pip install -r backend/requirements.txt -r frontend/requirements.txt -r requirements-dev.txt
pytest -q
```

The Docker build workflow builds backend and frontend images on pull requests and pushes. On tags matching `v*`, it can push images to GitHub Container Registry using the repository `GITHUB_TOKEN`.

## Production Limits

Before real production, add:

- authentication and authorization,
- managed secrets,
- managed PostgreSQL with backups,
- object storage for uploaded files,
- malware scanning for uploads,
- real migrations instead of startup schema patching,
- structured logs and alerting,
- proper CI test coverage with PostgreSQL service containers,
- cloud deployment manifests for ECS, Kubernetes or another managed runtime.

## Next Cloud Steps

- Split local and production Compose files.
- Add image version pinning and release notes.
- Add database migrations with Alembic.
- Add GitHub environments for staging and production approvals.
- Deploy backend/frontend images from GHCR to a cloud container service.
