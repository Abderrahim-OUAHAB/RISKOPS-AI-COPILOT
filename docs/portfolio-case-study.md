# Portfolio Case Study

## Context

AI RiskOps Copilot is a local portfolio release built to demonstrate AI Engineering, Data Engineering, Machine Learning, MLOps and LLMOps in one coherent product.

## Problem

Business teams often discover risk too late because signals are spread across documents, customer exports and operational systems. They need a practical way to prioritize customers and understand the reasons behind each risk.

## Users

- Customer success managers
- Revenue operations teams
- Risk managers
- Founders or operators reviewing weekly customer health

## Architecture

The system uses Streamlit for the dashboard, FastAPI for backend APIs, PostgreSQL for business data, pgvector for semantic search, XGBoost for churn scoring, LangGraph for controlled agent routing, Airflow/dbt for data pipelines and local monitoring for MLOps/LLMOps.

## Technical Choices

- FastAPI was chosen for typed APIs and automatic Swagger documentation.
- PostgreSQL keeps the data model realistic and interview-friendly.
- pgvector allows RAG without adding a separate vector database.
- XGBoost is a strong baseline for tabular churn prediction.
- MLflow tracks model experiments locally.
- Airflow and dbt show production-style data workflow thinking.
- LangGraph keeps agent routing explicit and controlled.
- JSONL traces provide a dependency-safe LLMOps fallback.
- Docker Compose makes the project reproducible on a laptop.

## Important Decisions

- Keep OpenAI optional for non-RAG demo paths.
- Avoid real AWS, auth and heavy production modules in the portfolio release.
- Prefer local artifacts and scripts over manual setup.
- Keep monitoring simple, inspectable and easy to explain.
- Use `/health` and `/ready` to separate liveness from demo readiness.

## Difficulties

- Keeping Docker builds reliable while Airflow/dbt/ML dependencies are heavy.
- Making scripts robust when the backend is not ready yet.
- Avoiding accidental `.env`, logs or generated reports in Git.
- Explaining agent behavior without overpromising autonomous AI.

## Results

- A working local AI product with backend, frontend, database, RAG, ML, agent, pipelines and monitoring.
- A one-command startup path.
- A demo seed script that prepares customer data, model artifacts, reports and traces.
- Recruiter-ready documentation and interview material.

## Limits

- No real cloud deployment yet.
- No authentication.
- The sample dataset is small.
- The monitoring report is lightweight.
- RAG answer generation requires an OpenAI API key.

## Next Steps

- Add AWS deployment.
- Add auth and role-based access.
- Add production-grade evaluation for RAG and ML.
- Add alerting for drift and failed traces.
- Add screenshots and demo video.

## Portfolio Sentence

AI RiskOps Copilot is a production-minded AI portfolio project that turns documents and customer data into explainable risk priorities using FastAPI, PostgreSQL, pgvector, RAG, XGBoost, LangGraph, Airflow, dbt and monitoring.

## Business Value

The project shows how AI can help a team move from scattered risk signals to prioritized actions. It gives managers a weekly view of customer risk, reasons and recommended actions.
