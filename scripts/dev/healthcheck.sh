#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

check_url() {
  local name="$1"
  local url="$2"
  local status
  status="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$url" || true)"
  echo "$name: $status"
}

check_url "Health" "http://localhost:8000/health"
check_url "Ready" "http://localhost:8000/ready"
check_url "Streamlit" "http://localhost:8501"
check_url "Airflow" "http://localhost:8080/login/"

echo ""
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  docker compose ps
else
  echo "Docker Compose is not available from this bash shell."
fi
