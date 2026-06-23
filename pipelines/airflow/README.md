# Airflow Pipeline

This folder contains the local Airflow setup for AI RiskOps Copilot.

The main DAG is `riskops_daily_pipeline`.

It orchestrates:

- FastAPI health check
- sample customer CSV import
- dbt model build
- dbt data tests
- churn model training
- weekly RiskOps report generation
- pipeline summary logging
