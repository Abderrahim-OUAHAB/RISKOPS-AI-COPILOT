import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


DEFAULT_API_URL = os.getenv("BACKEND_API_URL", "http://backend:8000").rstrip("/")
DEFAULT_OUTPUT_PATH = Path(
    os.getenv("PIPELINE_SUMMARY_PATH", "/opt/airflow/data/processed/pipeline_summary.json")
)


def generate_summary(api_url: str) -> dict[str, Any]:
    response = requests.get(f"{api_url}/reports/weekly-risk", timeout=120)
    response.raise_for_status()
    weekly_report = response.json()
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "weekly_report": weekly_report,
    }


def write_summary(summary: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the RiskOps pipeline summary.")
    parser.add_argument("--api-url", default=DEFAULT_API_URL)
    parser.add_argument("--output-path", default=str(DEFAULT_OUTPUT_PATH))
    args = parser.parse_args()

    summary = generate_summary(args.api_url.rstrip("/"))
    write_summary(summary, Path(args.output_path))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
