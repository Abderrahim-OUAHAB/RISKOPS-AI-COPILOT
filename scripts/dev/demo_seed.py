from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
API_URL = "http://localhost:8000"
SAMPLE_CUSTOMERS = PROJECT_ROOT / "data" / "sample" / "customers_sample.csv"
MODEL_PATH = PROJECT_ROOT / "ml" / "models" / "churn_model.pkl"
FEATURES_PATH = PROJECT_ROOT / "ml" / "models" / "churn_features.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a complete local RiskOps demo.")
    parser.add_argument("--api-url", default=API_URL)
    parser.add_argument("--force-train", action="store_true")
    args = parser.parse_args()

    api_url = args.api_url.rstrip("/")
    print("AI RiskOps Copilot demo seed")
    print(f"API: {api_url}")

    if not wait_for_backend(api_url):
        print("ERROR: backend is not ready. Start Docker first with scripts/dev/start.ps1.")
        return 1

    if not SAMPLE_CUSTOMERS.exists():
        print(f"ERROR: sample dataset missing: {SAMPLE_CUSTOMERS}")
        return 1

    steps: list[tuple[str, bool, Any]] = []
    steps.append(("health", True, request_json("GET", f"{api_url}/health")))
    steps.append(("ready", True, request_json("GET", f"{api_url}/ready", allow_error=True)))
    steps.append(("import_customers", True, upload_file(f"{api_url}/customers/import", SAMPLE_CUSTOMERS)))

    train_ok = ensure_model(force=args.force_train)
    steps.append(
        (
            "model_ready",
            train_ok,
            {
                "status": 200 if train_ok else 500,
                "body": {"model": str(MODEL_PATH), "features": str(FEATURES_PATH)},
            },
        )
    )

    steps.append(
        (
            "analyze_CUST-001",
            True,
            request_json(
                "POST",
                f"{api_url}/risk/analyze-customer",
                {"customer_id": "CUST-001"},
                allow_error=True,
            ),
        )
    )
    steps.append(("priority_customers", True, request_json("GET", f"{api_url}/risk/priority-customers")))
    steps.append(("weekly_risk", True, request_json("GET", f"{api_url}/reports/weekly-risk")))
    steps.append(
        (
            "monitoring_ml_report",
            True,
            request_json("POST", f"{api_url}/monitoring/ml/generate-report"),
        )
    )
    steps.append(
        (
            "agent_trace",
            True,
            request_json(
                "POST",
                f"{api_url}/agent/analyze",
                {"question": "Quels clients sont a risque cette semaine ?"},
            ),
        )
    )
    steps.append(("llm_summary", True, request_json("GET", f"{api_url}/monitoring/llm/summary")))

    print("\nDemo summary")
    success = True
    for name, expected_ok, payload in steps:
        ok = expected_ok and not is_error_payload(payload)
        success = success and ok
        print(f"- {name}: {'OK' if ok else 'CHECK'}")
        print(short_json(payload))

    print("\nUseful URLs")
    print("- FastAPI docs: http://localhost:8000/docs")
    print("- Streamlit: http://localhost:8501")
    print("- Airflow: http://localhost:8080")
    print("- Health: http://localhost:8000/health")
    print("- Ready: http://localhost:8000/ready")
    print("- MLflow: local ./mlruns directory")

    return 0 if success else 1


def wait_for_backend(api_url: str, timeout_seconds: int = 120) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            payload = request_json("GET", f"{api_url}/health")
            body = payload.get("body", {})
            if isinstance(body, dict) and body.get("status") in {"ok", "degraded"}:
                return True
        except Exception:
            pass
        time.sleep(3)
    return False


def ensure_model(force: bool = False) -> bool:
    if MODEL_PATH.exists() and FEATURES_PATH.exists() and not force:
        print("Model artifacts already present.")
        return True

    print("Training churn model...")
    result = subprocess.run(
        [sys.executable, "ml/training/train_churn_model.py"],
        cwd=PROJECT_ROOT,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: model training failed with exit code {result.returncode}")
        return False

    return MODEL_PATH.exists() and FEATURES_PATH.exists()


def request_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    allow_error: bool = False,
) -> dict[str, Any]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return decode_response(response.status, response.read())
    except urllib.error.HTTPError as exc:
        body = exc.read()
        decoded = decode_response(exc.code, body)
        if allow_error:
            return decoded
        return {"error": True, "status": exc.code, "body": decoded}
    except urllib.error.URLError as exc:
        return {"error": True, "status": "unreachable", "body": str(exc)}


def upload_file(url: str, path: Path) -> dict[str, Any]:
    boundary = "----riskops-demo-boundary"
    file_bytes = path.read_bytes()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
        "Content-Type: text/csv\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return decode_response(response.status, response.read())
    except urllib.error.HTTPError as exc:
        return {"error": True, "status": exc.code, "body": decode_response(exc.code, exc.read())}
    except urllib.error.URLError as exc:
        return {"error": True, "status": "unreachable", "body": str(exc)}


def decode_response(status_code: int, body: bytes) -> dict[str, Any]:
    text = body.decode("utf-8", errors="replace")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        payload = text[:500]
    return {"status": status_code, "body": payload}


def is_error_payload(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return True
    status = payload.get("status")
    return payload.get("error") is True or not isinstance(status, int) or status >= 400


def short_json(payload: Any) -> str:
    text = json.dumps(payload, ensure_ascii=True, indent=2)
    return text if len(text) <= 1200 else text[:1200] + "\n  ... truncated ..."


if __name__ == "__main__":
    raise SystemExit(main())
