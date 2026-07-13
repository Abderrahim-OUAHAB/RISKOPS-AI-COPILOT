# Product Screenshots

This folder contains the final GitHub portfolio screenshots for `v1.3.3-action-workflow`.

## Final Files

- `screenshot-executive-overview.png` - Streamlit Executive Overview.
- `screenshot-client-risk.png` - Client Risk after analyzing a sample customer alias.
- `screenshot-action-board.png` - Persisted Action Board with tracked actions.
- `screenshot-ai-assistant.png` - Controlled AI Assistant page.
- `screenshot-documents-rag.png` - Documents and RAG page.
- `screenshot-data-pipeline.png` - Data Pipeline page.
- `screenshot-monitoring.png` - Monitoring page.
- `screenshot-airflow-dag.png` - Airflow `riskops_daily_pipeline` DAG page.
- `screenshot-fastapi-docs.png` - FastAPI Swagger documentation.

## Capture Checklist

1. Start the local stack with Docker Compose.
2. Open Streamlit at `http://localhost:8501`.
3. Capture Executive Overview after the KPI cards and action plan load.
4. Capture Client Risk after selecting and analyzing a sample customer alias.
5. Capture Action Board after syncing recommended actions.
6. Capture Documents and RAG, AI Assistant, Data Pipeline and Monitoring from the sidebar.
7. Open Airflow at `http://localhost:8080`, sign in with the local demo account and capture `riskops_daily_pipeline`.
8. Open FastAPI docs at `http://localhost:8000/docs` and capture the endpoint list.

Do not capture `.env`, API keys, terminal logs, local credentials, generated trace files or private browser data.
