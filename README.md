# AI RiskOps Copilot

AI RiskOps Copilot is a full-stack AI portfolio project for customer risk operations.
It combines document intelligence, structured customer data, churn prediction, controlled AI agents, data pipelines and monitoring.
The goal is to show how an AI product can move from a demo chatbot to a production-minded decision support system.

## Business Problem

Risk signals are often scattered across contracts, CSV exports, invoices, support tickets and internal reports. A manager needs to know which customers are at risk, why they are risky, and what action to take first.

AI RiskOps Copilot answers questions like:

- Which customers are most likely to churn this week?
- Why is a customer risky?
- What actions should the team prioritize?
- What do uploaded documents say about a risk?
- Is the system healthy and ready for a demo or local deployment?

## Solution

The project provides a local AI application with:

- a Streamlit dashboard for users,
- a FastAPI backend for product APIs,
- PostgreSQL and pgvector for business data and vector search,
- PDF/CSV upload and document processing,
- RAG over processed document chunks,
- XGBoost churn prediction with MLflow tracking,
- a controlled LangGraph agent for routing questions,
- Airflow and dbt pipelines,
- MLOps and LLMOps monitoring,
- Docker and GitHub Actions for reproducibility.

## Architecture

![AI RiskOps Copilot architecture](docs/architecture-tech-map.svg)

Mermaid version: [docs/architecture-final.md](docs/architecture-final.md)

```text
Streamlit
  -> FastAPI
  -> PostgreSQL + pgvector
  -> RAG + OpenAI API
  -> XGBoost + MLflow
  -> LangGraph agent
  -> Airflow + dbt
  -> Monitoring reports + JSONL traces
```

## Technical Stack

- Backend: FastAPI, SQLAlchemy, Pydantic
- Frontend: Streamlit
- Database: PostgreSQL, pgvector
- RAG: OpenAI embeddings, LlamaIndex-ready services, vector search
- ML: XGBoost, scikit-learn, pandas, joblib
- MLOps: MLflow, local data quality report
- LLMOps: JSONL traces, optional Langfuse export
- Data engineering: Airflow, dbt
- DevOps: Docker Compose, GitHub Actions

## Features

- Upload PDF and CSV files.
- Store document metadata in PostgreSQL.
- Extract PDF text and CSV content.
- Chunk document text.
- Create embeddings and store vectors with pgvector.
- Ask RAG questions with source chunks.
- Import sample customer data from CSV.
- Train a churn model.
- Analyze customer risk.
- List priority customers.
- Generate a weekly risk report.
- Route controlled business questions with LangGraph.
- Generate an ML monitoring HTML report.
- Trace RAG and agent calls locally.
- Check health and readiness.

## Main Endpoints

- `GET /health`
- `GET /ready`
- `POST /documents/upload`
- `POST /documents/{document_id}/process`
- `GET /documents`
- `GET /documents/{document_id}`
- `POST /rag/ask`
- `POST /customers/import`
- `GET /customers`
- `POST /risk/analyze-customer`
- `GET /risk/priority-customers`
- `GET /risk/history`
- `GET /reports/weekly-risk`
- `POST /agent/analyze`
- `POST /monitoring/ml/generate-report`
- `GET /monitoring/ml/report`
- `GET /monitoring/ml/report?format=html`
- `GET /monitoring/llm/traces`
- `GET /monitoring/llm/summary`

## How To Run

Recommended on Windows PowerShell:

```powershell
scripts/dev/start.ps1
```

Alternative if PowerShell execution policy blocks local scripts:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev/start.ps1
```

Cross-platform Docker command:

```bash
docker compose up -d --build
```

Bash helper scripts are also available under `scripts/dev/*.sh`. On Windows, prefer the PowerShell scripts unless Docker Desktop is integrated with your WSL shell.

Useful URLs:

- FastAPI docs: http://localhost:8000/docs
- Streamlit: http://localhost:8501
- Airflow: http://localhost:8080
- Health: http://localhost:8000/health
- Ready: http://localhost:8000/ready
- MLflow: local `./mlruns` directory

Docker build note:

- Cached rebuild measured locally during the portfolio release: about 14 seconds.
- A first uncached build can take several minutes because backend ML/RAG packages and Airflow/dbt packages are installed.
- `.env` is optional for Docker Compose; secrets are not required for local CI validation.

## Demo Mode

Prepare a complete local demo:

```powershell
scripts/dev/demo-seed.ps1
```

Alternative:

```powershell
python scripts/dev/demo_seed.py
```

The demo seed script:

- waits for the backend,
- imports `data/sample/customers_sample.csv`,
- verifies or trains the churn model,
- analyzes `CUST-001`,
- lists priority customers,
- generates the weekly risk report,
- generates the ML monitoring report,
- creates an agent trace,
- prints a final summary and useful URLs.

## Screenshots

Suggested screenshots for a portfolio page:

- `docs/screenshots/streamlit-dashboard.png`
- `docs/screenshots/fastapi-docs.png`
- `docs/screenshots/airflow-dag.png`
- `docs/screenshots/ml-monitoring-report.png`
- `docs/screenshots/llm-traces.png`

The screenshot directory is intentionally not required for the app to run.

## Data Pipeline

Airflow orchestrates the local workflow. dbt builds analytics models from PostgreSQL data:

- `stg_customers`
- `int_customer_risk_features`
- `mart_customer_risk_summary`

The pipeline demonstrates ingestion, transformation, testing and reporting without requiring a cloud platform.

## ML Pipeline

The churn pipeline uses the sample customer dataset or PostgreSQL data when available. It trains an XGBoost classifier, logs metrics with MLflow, and writes model artifacts to `ml/models`.

Model outputs are used by:

- `POST /risk/analyze-customer`
- `GET /risk/priority-customers`
- `GET /reports/weekly-risk`
- `POST /agent/analyze`

## RAG Pipeline

The document pipeline uploads PDF/CSV files, extracts text, chunks content, creates embeddings and stores vectorized chunks with pgvector. `/rag/ask` retrieves relevant chunks and returns an answer with sources.

OpenAI is optional for non-RAG demo paths. If no API key is configured, customer risk, reporting, monitoring and agent priority routing still work.

## LangGraph Agent

The agent is intentionally controlled. It routes questions to known tools:

- customer analysis,
- priority customers,
- weekly report,
- RAG over documents,
- fallback guidance.

This makes the system easier to defend in an interview than an uncontrolled free-form agent.

## Monitoring

MLOps:

- `POST /monitoring/ml/generate-report` creates `monitoring/reports/ml_data_quality_report.html`.
- The report compares reference sample data with current PostgreSQL customers.
- It checks missing values and simple feature drift for tenure, charges, support tickets and late payments.
- Evidently is treated as an optional monitoring concept; the app keeps a dependency-safe local HTML fallback.

LLMOps:

- `POST /rag/ask` and `POST /agent/analyze` are traced.
- Local traces are written to `monitoring/logs/llm_traces.jsonl`.
- Traces capture timestamp, question, selected tool, latency, status, errors, source count and document id.
- Langfuse export is optional and protected by environment variables.

Health:

- `/health` reports API, database, model and pgvector status.
- `/ready` verifies database connectivity, required tables, model artifact and monitoring folders.

## Limits

- This is a local portfolio release, not a cloud deployment.
- Authentication and authorization are intentionally out of scope.
- The RAG path needs an OpenAI API key for embeddings and generated answers.
- The ML dataset is small and designed for demonstration.
- The monitoring report is lightweight and local.
- No real AWS infrastructure is created in this version.

## Roadmap

- Add authentication for multi-user access.
- Deploy to AWS with managed PostgreSQL and container hosting.
- Add real alerting for drift and failed traces.
- Add stronger evaluation for RAG answers.
- Add CI tests with a temporary PostgreSQL service.
- Add screenshots and a short demo video.

## What This Project Demonstrates

- Product thinking around a business risk use case.
- Backend API design with FastAPI.
- Relational and vector data modeling.
- RAG architecture with source traceability.
- Machine learning training and serving.
- MLOps and LLMOps basics.
- Data engineering orchestration with Airflow and dbt.
- Dockerized local development.
- Recruiter-ready documentation and demo flow.

## Interview Questions To Prepare

- Why is this more than a chatbot?
- How does pgvector support RAG?
- Why use a controlled LangGraph agent?
- What happens when OpenAI is unavailable?
- How do `/health` and `/ready` differ?
- What does the ML monitoring report detect?
- How would you deploy this on AWS?
- What would you improve before production?

See also:

- [docs/portfolio-case-study.md](docs/portfolio-case-study.md)
- [docs/interview-pitch.md](docs/interview-pitch.md)
- [docs/interview-qa.md](docs/interview-qa.md)
- [docs/demo-script.md](docs/demo-script.md)
