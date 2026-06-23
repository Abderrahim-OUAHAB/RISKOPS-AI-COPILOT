# dbt Project

This folder contains the RiskOps dbt project.

The dbt project lives in `riskops_dbt/` and builds:

- `stg_customers`
- `int_customer_risk_features`
- `mart_customer_risk_summary`

The models transform PostgreSQL customer data into tested analytics tables in the `analytics` schema.
