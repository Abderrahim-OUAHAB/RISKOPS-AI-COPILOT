#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

echo "Starting AI RiskOps Copilot with Docker..."
SECONDS=0
docker compose up -d --build
echo "Docker build/start completed in ${SECONDS}s."

bash scripts/dev/healthcheck.sh

cat <<'URLS'

Useful URLs
- FastAPI docs: http://localhost:8000/docs
- Streamlit: http://localhost:8501
- Airflow: http://localhost:8080
- Health: http://localhost:8000/health
- Ready: http://localhost:8000/ready
- MLflow: local ./mlruns directory
URLS
