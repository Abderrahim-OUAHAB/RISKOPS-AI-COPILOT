# AI RiskOps Copilot

AI RiskOps Copilot is a portfolio project that demonstrates AI Engineering, Data Engineering, Machine Learning, MLOps and LLMOps skills.

The goal is to build an AI assistant that helps a company detect business risks from documents, customer data and operational signals.

## Business Problem

Companies often store important risk signals across many sources:

- contracts
- invoices
- customer files
- support tickets
- sales CSV files
- internal reports

Managers need fast answers to questions like:

- Which customers may churn this week?
- Which invoices look risky?
- Which contracts contain risky clauses?
- Which support tickets are urgent?
- Which actions should the team take first?

This project solves that problem with a complete AI system, not a simple chatbot.

## MVP Scope

The first version focuses on:

- FastAPI backend
- Streamlit dashboard
- PostgreSQL database
- pgvector semantic search
- PDF and CSV upload foundation
- RAG document processing with sources
- OpenAI embeddings
- XGBoost churn prediction
- MLflow experiment tracking
- RiskOps scoring and prioritization
- prediction history
- controlled LangGraph agent
- Airflow orchestration
- dbt analytics models and data tests
- churn risk dataset sample
- Docker setup

Future versions will add:

- Langfuse and Evidently AI monitoring
- AWS deployment

## Architecture

Visual architecture:

![AI RiskOps Copilot architecture](docs/architecture-tech-map.svg)

```text
User
  -> Streamlit dashboard
  -> FastAPI backend
  -> PostgreSQL + pgvector
  -> LlamaIndex RAG
  -> XGBoost churn model
  -> LangGraph decision agent
  -> Airflow + dbt data pipelines
  -> MLflow, Langfuse, Evidently AI
```

## Project Structure

```text
riskops-ai-copilot/
  backend/          FastAPI application
  frontend/         Streamlit dashboard
  ml/               ML training and model artifacts
  data/             raw, processed and sample data
  pipelines/        Airflow DAGs, dbt project and pipeline scripts
  docs/             project documentation
  scripts/          database initialization scripts
```

## Quick Start

1. Copy the environment file.

```bash
cp .env.example .env
```

2. Start the project.

```bash
docker compose up --build
```

3. Open the services.

- Backend API: `http://localhost:8000`
- API health: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`
- Streamlit dashboard: `http://localhost:8501`
- Airflow UI: `http://localhost:8080` (`admin` / `admin`)

## Backend Endpoints

- `GET /health`: API health check.
- `POST /documents/upload`: upload one PDF or CSV file and store metadata in PostgreSQL.
- `POST /documents/{document_id}/process`: extract text, chunk it, create embeddings and store chunks in pgvector.
- `GET /documents`: list uploaded documents.
- `GET /documents/{document_id}`: get one document by id.
- `POST /rag/ask`: ask a question against processed document chunks and return sourced answers.
- `POST /customers/import`: import customer churn data from CSV.
- `GET /customers`: list imported customers.
- `GET /customers/{customer_id}`: get one customer by external id.
- `POST /risk/predict`: predict churn risk for one customer.
- `GET /risk/customers`: list customers with their latest risk score.
- `POST /risk/analyze-customer`: calculate RiskOps score, reasons, actions and save prediction history.
- `GET /risk/priority-customers`: list customers sorted by business risk priority.
- `GET /risk/history`: list recent risk predictions, optionally filtered by `customer_id`.
- `GET /reports/weekly-risk`: generate the weekly RiskOps report.
- `POST /agent/analyze`: route a controlled RiskOps question through a LangGraph workflow.

Uploaded files are stored in `data/raw`.

## Environment Variables

The OpenAI API key must stay in `.env` and must never be committed.

```bash
OPENAI_API_KEY=replace_with_your_key_later
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o-mini
CHURN_MODEL_PATH=ml/models/churn_model.pkl
CHURN_FEATURES_PATH=ml/models/churn_features.json
MLFLOW_TRACKING_URI=file:./mlruns
MLFLOW_EXPERIMENT_NAME=riskops-churn-model
AIRFLOW_UID=50000
AIRFLOW_PROJ_DIR=./pipelines
DBT_PROFILES_DIR=/opt/airflow/pipelines/dbt/riskops_dbt
DBT_TARGET=dev
```

Without a real `OPENAI_API_KEY`, upload and listing still work. Document processing returns a clear error because embeddings require OpenAI.
MLflow stores local experiment runs under `mlruns/`, which is ignored by Git.

## Data Pipeline

The project includes a local Data Engineering layer with Airflow and dbt.

Airflow orchestrates the daily workflow in `riskops_daily_pipeline`:

1. `health_check_api`: checks that FastAPI is reachable.
2. `import_sample_customers`: imports `data/sample/customers_sample.csv`.
3. `run_dbt_models`: builds dbt staging, intermediate and mart models.
4. `run_dbt_tests`: runs dbt data quality tests.
5. `train_churn_model`: refreshes the XGBoost churn model.
6. `generate_weekly_risk_report`: calls the weekly RiskOps report API.
7. `pipeline_summary`: prints a short summary for Airflow logs.

dbt transforms PostgreSQL customer data into analytics tables in the `analytics` schema:

- `stg_customers`: cleans customer data, casts numeric columns and normalizes `contract_type`.
- `int_customer_risk_features`: creates business flags such as support, payment, tenure and high-value risk.
- `mart_customer_risk_summary`: creates a dashboard-ready customer risk summary.

dbt tests validate:

- `customer_id` is not null.
- `customer_id` is unique.
- `monthly_charges` is not null.
- `tenure` is not null.

Useful dbt commands inside the Airflow container:

```bash
docker compose exec airflow-scheduler dbt debug --project-dir /opt/airflow/pipelines/dbt/riskops_dbt --profiles-dir /opt/airflow/pipelines/dbt/riskops_dbt
docker compose exec airflow-scheduler dbt run --project-dir /opt/airflow/pipelines/dbt/riskops_dbt --profiles-dir /opt/airflow/pipelines/dbt/riskops_dbt
docker compose exec airflow-scheduler dbt test --project-dir /opt/airflow/pipelines/dbt/riskops_dbt --profiles-dir /opt/airflow/pipelines/dbt/riskops_dbt
```

Current limitations:

- Airflow uses a local development configuration, not a production executor setup.
- The pipeline imports a sample CSV and is idempotent through the existing customer upsert logic.
- dbt models are analytics tables only; the ML script still trains from the application `customers` table.
- Airflow writes its local MLflow/model artifacts to `/tmp` to avoid Windows bind mount permission issues.
- Monitoring tools such as Langfuse and Evidently AI are intentionally left for later.

## Local Test Commands

Start the stack:

```bash
docker compose up --build
```

Check the API:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/documents
```

Upload the sample CSV:

```bash
curl -F "file=@data/sample/customers_sample.csv" http://localhost:8000/documents/upload
```

Process a document:

```bash
curl -X POST http://localhost:8000/documents/1/process
```

Ask a RAG question:

```bash
curl -X POST http://localhost:8000/rag/ask \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"Resume les risques principaux\",\"document_id\":1}"
```

Get one document:

```bash
curl http://localhost:8000/documents/1
```

Import customers:

```bash
curl -X POST http://localhost:8000/customers/import -F "file=@data/sample/customers_sample.csv"
curl http://localhost:8000/customers
```

Train the churn model:

```bash
python ml/training/train_churn_model.py
```

Predict customer risk:

```bash
curl -X POST http://localhost:8000/risk/predict \
  -H "Content-Type: application/json" \
  -d "{\"customer_id\":\"CUST-001\"}"
```

Example response:

```json
{
  "customer_id": "CUST-001",
  "churn_probability": 0.82,
  "risk_score": 82,
  "risk_level": "high",
  "reasons": [
    "Many support tickets",
    "Late payments detected",
    "Short customer tenure"
  ]
}
```

Batch risk:

```bash
curl http://localhost:8000/risk/customers
```

Analyze one customer with RiskOps scoring:

```bash
curl -X POST http://localhost:8000/risk/analyze-customer \
  -H "Content-Type: application/json" \
  -d "{\"customer_id\":\"CUST-001\"}"
```

Example RiskOps response:

```json
{
  "customer_id": "CUST-001",
  "risk_score": 82,
  "risk_level": "high",
  "churn_probability": 0.81,
  "reasons": [
    "High churn probability",
    "Late payments detected",
    "Many support tickets"
  ],
  "recommended_actions": [
    "Contact customer within 48 hours",
    "Review unpaid invoices",
    "Escalate recent support issues"
  ],
  "prediction_id": 1
}
```

Priority, history and weekly report:

```bash
curl http://localhost:8000/risk/priority-customers
curl http://localhost:8000/risk/history
curl http://localhost:8000/reports/weekly-risk
```

Ask the controlled RiskOps agent:

```bash
curl -X POST http://localhost:8000/agent/analyze \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"Quels clients sont a risque cette semaine ?\"}"
```

Example agent response:

```json
{
  "answer": "5 clients prioritaires identifies. Le plus urgent est CUST-001 avec un score de 82/100.",
  "selected_tool": "priority_customers",
  "data": {},
  "sources": []
}
```

The RiskOps score combines churn probability, late payments, support tickets, short tenure, month-to-month contracts and high-value exposure. It is a demo scoring layer, not a regulated credit or financial risk model.

Run the Data Engineering pipeline checks:

```bash
python -m compileall backend/app frontend/app.py ml/training pipelines
docker compose config
docker compose up -d --build
curl http://localhost:8000/health
curl http://localhost:8000/customers
curl -X POST http://localhost:8000/customers/import -F "file=@data/sample/customers_sample.csv"
python ml/training/train_churn_model.py
curl http://localhost:8000/reports/weekly-risk
```

## Interview Pitch

I built AI RiskOps Copilot to show how an AI product can combine documents, structured data, machine learning and monitoring to help companies detect business risk. The MVP includes a FastAPI backend, PostgreSQL with pgvector, RAG with sources, XGBoost churn prediction, MLflow tracking, RiskOps prioritization, a controlled LangGraph agent, Airflow orchestration, dbt analytics models, a Streamlit dashboard and Docker. The next modules add production monitoring.
