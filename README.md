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
- churn risk dataset sample
- Docker setup

Future versions will add:

- LangGraph agent
- Risk Score
- Airflow and dbt pipelines
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
  -> MLflow, Langfuse, Evidently AI
```

## Project Structure

```text
riskops-ai-copilot/
  backend/          FastAPI application
  frontend/         Streamlit dashboard
  ml/               ML training and model artifacts
  data/             raw, processed and sample data
  pipelines/        Airflow and dbt future modules
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
```

Without a real `OPENAI_API_KEY`, upload and listing still work. Document processing returns a clear error because embeddings require OpenAI.
MLflow stores local experiment runs under `mlruns/`, which is ignored by Git.

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

## Interview Pitch

I built AI RiskOps Copilot to show how an AI product can combine documents, structured data, machine learning and monitoring to help companies detect business risk. The MVP includes a FastAPI backend, PostgreSQL with pgvector, RAG with sources, XGBoost churn prediction, MLflow tracking, a Streamlit dashboard and Docker. The next modules add LangGraph agents, orchestration and production monitoring.
