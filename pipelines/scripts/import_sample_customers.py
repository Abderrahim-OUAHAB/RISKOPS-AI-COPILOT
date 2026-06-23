import argparse
import os
import time
from pathlib import Path
from typing import Any

import requests


DEFAULT_API_URL = os.getenv("BACKEND_API_URL", "http://backend:8000").rstrip("/")
DEFAULT_SAMPLE_PATH = Path(
    os.getenv("SAMPLE_CUSTOMERS_PATH", "/opt/airflow/data/sample/customers_sample.csv")
)


def wait_for_backend(api_url: str, retries: int = 20, delay_seconds: float = 3.0) -> dict[str, Any]:
    last_error: Exception | None = None
    for _ in range(retries):
        try:
            response = requests.get(f"{api_url}/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(delay_seconds)

    raise RuntimeError(f"Backend is not ready: {last_error}")


def import_sample_customers(api_url: str, sample_path: Path) -> dict[str, Any]:
    if not sample_path.exists():
        raise FileNotFoundError(f"Sample customer CSV not found: {sample_path}")

    with sample_path.open("rb") as csv_file:
        response = requests.post(
            f"{api_url}/customers/import",
            files={"file": (sample_path.name, csv_file, "text/csv")},
            timeout=60,
        )
    response.raise_for_status()
    return response.json()


def main() -> None:
    parser = argparse.ArgumentParser(description="Import sample RiskOps customers.")
    parser.add_argument("--api-url", default=DEFAULT_API_URL)
    parser.add_argument("--sample-path", default=str(DEFAULT_SAMPLE_PATH))
    parser.add_argument("--health-only", action="store_true")
    args = parser.parse_args()

    api_url = args.api_url.rstrip("/")
    health = wait_for_backend(api_url)
    print({"health": health})

    if args.health_only:
        return

    result = import_sample_customers(api_url, Path(args.sample_path))
    print(result)


if __name__ == "__main__":
    main()
