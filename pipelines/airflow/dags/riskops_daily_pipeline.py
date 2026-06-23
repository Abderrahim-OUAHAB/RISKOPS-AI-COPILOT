import json
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator


PIPELINES_DIR = Path("/opt/airflow/pipelines")
SCRIPTS_DIR = PIPELINES_DIR / "scripts"
ML_DIR = Path("/opt/airflow/ml")
SUMMARY_PATH = Path("/opt/airflow/data/processed/pipeline_summary.json")


default_args = {
    "owner": "riskops",
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}


def print_pipeline_summary() -> None:
    if not SUMMARY_PATH.exists():
        print("No pipeline summary generated yet.")
        return
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    weekly_report = summary.get("weekly_report", {})
    print(
        {
            "generated_at": summary.get("generated_at"),
            "total_customers": weekly_report.get("total_customers"),
            "high_risk_customers": weekly_report.get("high_risk_customers"),
            "executive_summary": weekly_report.get("executive_summary"),
        }
    )


with DAG(
    dag_id="riskops_daily_pipeline",
    description="Daily RiskOps data pipeline with API import, dbt, ML and report generation.",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["riskops", "dbt", "ml"],
) as dag:
    health_check_api = BashOperator(
        task_id="health_check_api",
        bash_command=f"python {SCRIPTS_DIR / 'import_sample_customers.py'} --health-only",
    )

    import_sample_customers = BashOperator(
        task_id="import_sample_customers",
        bash_command=f"python {SCRIPTS_DIR / 'import_sample_customers.py'}",
    )

    run_dbt_models = BashOperator(
        task_id="run_dbt_models",
        bash_command=f"python {SCRIPTS_DIR / 'run_dbt.py'} run",
    )

    run_dbt_tests = BashOperator(
        task_id="run_dbt_tests",
        bash_command=f"python {SCRIPTS_DIR / 'run_dbt.py'} test",
    )

    train_churn_model = BashOperator(
        task_id="train_churn_model",
        bash_command=f"cd /opt/airflow && PYTHONPATH=/opt/airflow/backend python {ML_DIR / 'training' / 'train_churn_model.py'}",
    )

    generate_weekly_risk_report = BashOperator(
        task_id="generate_weekly_risk_report",
        bash_command=f"python {SCRIPTS_DIR / 'generate_pipeline_summary.py'}",
    )

    pipeline_summary = PythonOperator(
        task_id="pipeline_summary",
        python_callable=print_pipeline_summary,
    )

    (
        health_check_api
        >> import_sample_customers
        >> run_dbt_models
        >> run_dbt_tests
        >> train_churn_model
        >> generate_weekly_risk_report
        >> pipeline_summary
    )
