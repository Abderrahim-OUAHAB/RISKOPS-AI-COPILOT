# Interview Pitch

## 30-Second Pitch

AI RiskOps Copilot is a full-stack AI product that helps a business team detect customer risk. It combines uploaded documents, customer data, churn prediction, RAG, a controlled LangGraph agent, Airflow/dbt pipelines and monitoring. The important point is that it is not just a chatbot: it connects AI answers to data, model outputs, sources, traces and operational health checks.

## 2-Minute Pitch

I built AI RiskOps Copilot as a portfolio project to show an end-to-end AI engineering workflow. The business problem is that customer risk signals are spread across documents, CRM exports and operational metrics. A manager wants to know which customers need attention, why, and what actions to take.

The application has a Streamlit dashboard and a FastAPI backend. PostgreSQL stores customers, documents, chunks and predictions. pgvector supports semantic retrieval for RAG. The ML part trains an XGBoost churn model and tracks experiments with MLflow. The agent part uses LangGraph in a controlled way: it routes a question to customer analysis, priority customers, weekly reporting or RAG. The data engineering layer uses Airflow and dbt. The monitoring layer adds health checks, readiness checks, ML data quality reports and LLM traces.

For a demo, I can start Docker, seed the sample dataset, train or verify the model, generate a weekly risk report, create a monitoring report and show an agent trace.

## Technical Pitch

The project is organized around clear service boundaries:

- Streamlit for the user interface.
- FastAPI for API contracts.
- SQLAlchemy and Pydantic for data access and validation.
- PostgreSQL for structured entities.
- pgvector for embeddings.
- XGBoost for churn scoring.
- MLflow for experiment tracking.
- Airflow and dbt for data orchestration.
- LangGraph for controlled agent routing.
- JSONL traces and optional Langfuse for LLMOps.
- Docker Compose for local reproducibility.

## Architecture Explanation

The user interacts with Streamlit. Streamlit calls FastAPI. FastAPI reads and writes PostgreSQL, calls ML services, RAG services and the agent service. PostgreSQL stores customer data, documents, chunks and predictions. pgvector stores embeddings for semantic search. Airflow and dbt prepare analytical data and run scheduled jobs. Monitoring endpoints expose system status, readiness, ML report status and LLM traces.

## RAG Explanation

The RAG pipeline starts with a PDF or CSV upload. The backend extracts text, splits it into chunks, creates embeddings and stores them in PostgreSQL with pgvector. When the user asks a question, the system retrieves the most similar chunks and uses them as context. The answer includes sources so the user can understand where the answer came from.

## ML Explanation

The ML pipeline predicts churn risk from structured customer features such as tenure, monthly charges, total charges, contract type, support tickets and late payments. XGBoost produces churn probability, then the business layer turns that probability into a RiskOps score, risk level, reasons and recommended actions.

## Data Engineering Explanation

Airflow orchestrates the local pipeline. dbt transforms raw customer data into staging, intermediate and mart models. This shows that the AI product is connected to a data workflow, not only to isolated API endpoints.

## MLOps And LLMOps Explanation

MLOps is represented by model artifacts, MLflow tracking and a local data quality report. LLMOps is represented by traces for RAG and agent calls. Each trace stores latency, status, selected tool, question, errors and source count. Langfuse can be enabled later without breaking the local fallback.

## What I Learned

- How to connect AI features to real backend architecture.
- How to keep agent behavior controlled and explainable.
- How to separate product APIs, ML services, RAG services and monitoring.
- How to make a demo reproducible with Docker and scripts.
- How to discuss limitations honestly in an interview.

## Why This Is Different From A Simple Chatbot

A chatbot only answers text prompts. This project uses persistent data, document ingestion, vector search, model scoring, orchestration, monitoring and operational checks. It can explain which customer is risky, why the model thinks so, which action to take and whether the system is ready to run.

