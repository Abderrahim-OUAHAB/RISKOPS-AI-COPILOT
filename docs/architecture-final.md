# Final Architecture

```mermaid
flowchart LR
    user[Business user] --> streamlit[Streamlit dashboard]
    streamlit --> api[FastAPI backend]

    api --> postgres[(PostgreSQL)]
    postgres --> pgvector[pgvector embeddings]

    api --> upload[PDF/CSV upload]
    upload --> chunks[Text extraction and chunks]
    chunks --> openai[OpenAI API]
    openai --> pgvector
    pgvector --> rag[RAG answer with sources]
    rag --> api

    api --> ml[XGBoost churn model]
    ml --> mlflow[MLflow local tracking]
    ml --> risk[Risk score and recommendations]

    api --> agent[LangGraph controlled agent]
    agent --> risk
    agent --> rag
    agent --> report[Weekly risk report]

    airflow[Airflow DAG] --> dbt[dbt models and tests]
    dbt --> postgres
    airflow --> ml
    airflow --> report

    api --> health[/health and /ready]
    api --> traces[monitoring/logs/llm_traces.jsonl]
    api --> mlreport[Evidently-style ML HTML report]
    traces -. optional export .-> langfuse[Langfuse optional]

    github[GitHub Actions] --> compile[Compile Python]
    github --> compose[Validate Docker Compose]
```

## Notes

- PostgreSQL stores structured data and document metadata.
- pgvector stores embeddings for semantic retrieval.
- OpenAI is optional for non-RAG demo paths.
- MLflow writes to local `mlruns`.
- Monitoring artifacts are local and ignored by Git except `.gitkeep`.
- Docker Compose starts postgres, backend, frontend, airflow-webserver and airflow-scheduler.
