from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings

REFERENCE_DATA_PATH = Path("data/sample/customers_sample.csv")
MONITORED_COLUMNS = [
    "support_tickets",
    "late_payments",
    "monthly_charges",
    "total_charges",
    "tenure",
]


def generate_ml_monitoring_report(db: Session | None = None) -> dict[str, Any]:
    reference = load_reference_dataset()
    current = load_current_dataset(db)
    if current.empty:
        current = reference.copy()
        current_source = "reference_fallback"
    else:
        current_source = "postgres"

    summary = build_monitoring_summary(reference, current, current_source)
    html = build_html_report(summary, reference, current)
    report_path = Path(settings.ml_monitoring_report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(html, encoding="utf-8")

    return {
        "report_exists": True,
        "report_path": str(report_path),
        "generated_at": summary["generated_at"],
        "summary": summary,
    }


def get_ml_report_status() -> dict[str, Any]:
    report_path = Path(settings.ml_monitoring_report_path)
    generated_at = None
    if report_path.exists():
        generated_at = datetime.fromtimestamp(
            report_path.stat().st_mtime,
            tz=timezone.utc,
        ).isoformat()

    return {
        "report_exists": report_path.exists(),
        "report_path": str(report_path),
        "generated_at": generated_at,
        "summary": "ML monitoring report is available."
        if report_path.exists()
        else "ML monitoring report has not been generated yet.",
    }


def load_reference_dataset() -> pd.DataFrame:
    if not REFERENCE_DATA_PATH.exists():
        raise FileNotFoundError(f"Reference dataset not found: {REFERENCE_DATA_PATH}")
    return pd.read_csv(REFERENCE_DATA_PATH)


def load_current_dataset(db: Session | None) -> pd.DataFrame:
    if db is None:
        return pd.DataFrame()

    query = text(
        """
        SELECT
            customer_external_id AS customer_id,
            name,
            tenure,
            monthly_charges,
            total_charges,
            contract_type,
            support_tickets,
            late_payments,
            churn
        FROM customers
        WHERE customer_external_id IS NOT NULL
        """
    )
    try:
        return pd.read_sql(query, db.bind)
    except Exception:
        return pd.DataFrame()


def build_monitoring_summary(
    reference: pd.DataFrame,
    current: pd.DataFrame,
    current_source: str,
) -> dict[str, Any]:
    reference = normalize_columns(reference)
    current = normalize_columns(current)
    missing_values = {
        column: int(current[column].isna().sum())
        for column in MONITORED_COLUMNS
        if column in current.columns
    }
    drift = calculate_simple_drift(reference, current)

    warnings: list[str] = []
    if len(reference) < 10 or len(current) < 10:
        warnings.append("Dataset is small; drift checks are directional only.")
    if current_source == "reference_fallback":
        warnings.append("PostgreSQL dataset is empty or unavailable; reference data was used.")

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "reference_rows": int(len(reference)),
        "current_rows": int(len(current)),
        "current_source": current_source,
        "monitored_columns": MONITORED_COLUMNS,
        "missing_values": missing_values,
        "drift": drift,
        "warnings": warnings,
        "evidently_available": is_evidently_available(),
    }


def normalize_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    normalized = dataframe.copy()
    for column in MONITORED_COLUMNS:
        if column in normalized.columns:
            normalized[column] = pd.to_numeric(normalized[column], errors="coerce")
    return normalized


def calculate_simple_drift(
    reference: pd.DataFrame,
    current: pd.DataFrame,
) -> dict[str, dict[str, float | bool | None]]:
    drift: dict[str, dict[str, float | bool | None]] = {}
    for column in MONITORED_COLUMNS:
        if column not in reference.columns or column not in current.columns:
            drift[column] = {
                "reference_mean": None,
                "current_mean": None,
                "relative_mean_change": None,
                "drift_detected": False,
            }
            continue

        reference_mean = pd.to_numeric(reference[column], errors="coerce").mean()
        current_mean = pd.to_numeric(current[column], errors="coerce").mean()
        if pd.isna(reference_mean) or pd.isna(current_mean):
            relative_change = None
            drift_detected = False
        else:
            denominator = abs(reference_mean) if abs(reference_mean) > 1e-9 else 1.0
            relative_change = float(abs(current_mean - reference_mean) / denominator)
            drift_detected = relative_change >= 0.25

        drift[column] = {
            "reference_mean": round(float(reference_mean), 4)
            if not pd.isna(reference_mean)
            else None,
            "current_mean": round(float(current_mean), 4)
            if not pd.isna(current_mean)
            else None,
            "relative_mean_change": round(relative_change, 4)
            if relative_change is not None
            else None,
            "drift_detected": drift_detected,
        }
    return drift


def is_evidently_available() -> bool:
    try:
        import evidently  # noqa: F401
    except Exception:
        return False
    return True


def build_html_report(
    summary: dict[str, Any],
    reference: pd.DataFrame,
    current: pd.DataFrame,
) -> str:
    drift_rows = "".join(
        "<tr>"
        f"<td>{column}</td>"
        f"<td>{values['reference_mean']}</td>"
        f"<td>{values['current_mean']}</td>"
        f"<td>{values['relative_mean_change']}</td>"
        f"<td>{values['drift_detected']}</td>"
        "</tr>"
        for column, values in summary["drift"].items()
    )
    missing_rows = "".join(
        f"<tr><td>{column}</td><td>{count}</td></tr>"
        for column, count in summary["missing_values"].items()
    )
    warnings = "".join(f"<li>{warning}</li>" for warning in summary["warnings"])

    return f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>RiskOps ML Monitoring Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #1f2937; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0; }}
    th, td {{ border: 1px solid #d1d5db; padding: 8px; text-align: left; }}
    th {{ background: #f3f4f6; }}
    .ok {{ color: #047857; }}
  </style>
</head>
<body>
  <h1>RiskOps ML Monitoring Report</h1>
  <p>Generated at: {summary['generated_at']}</p>
  <p>Reference rows: {summary['reference_rows']} | Current rows: {summary['current_rows']}</p>
  <p>Current source: {summary['current_source']}</p>
  <p>Evidently package available: {summary['evidently_available']}</p>
  <h2>Data Quality</h2>
  <table><tr><th>Column</th><th>Missing values</th></tr>{missing_rows}</table>
  <h2>Simple Drift Check</h2>
  <table>
    <tr><th>Column</th><th>Reference mean</th><th>Current mean</th><th>Relative change</th><th>Drift detected</th></tr>
    {drift_rows}
  </table>
  <h2>Warnings</h2>
  <ul>{warnings or '<li class="ok">No warning.</li>'}</ul>
  <h2>Dataset Preview</h2>
  <h3>Reference</h3>
  {reference.head(10).to_html(index=False)}
  <h3>Current</h3>
  {current.head(10).to_html(index=False)}
</body>
</html>
"""
