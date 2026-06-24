# Demo Script

## Preparation Before Recording

1. Run `scripts/dev/start.ps1`.
2. Run `scripts/dev/demo-seed.ps1`.
3. Open:
   - http://localhost:8501
   - http://localhost:8000/docs
   - http://localhost:8080
   - http://localhost:8000/monitoring/ml/report?format=html
4. Confirm `/health` and `/ready` return OK.

If PowerShell blocks scripts, use:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev/start.ps1
powershell -ExecutionPolicy Bypass -File scripts/dev/demo-seed.ps1
```

## 2-Minute Demo

1. Show Streamlit dashboard.
Say: "This is AI RiskOps Copilot, a local AI product for customer risk operations."

2. Show priority customers.
Say: "The system combines structured customer data and a churn model to prioritize accounts."

3. Show FastAPI docs.
Say: "The backend exposes clear APIs for documents, RAG, risk, reports, agents and monitoring."

4. Show the monitoring report.
Say: "The demo also includes MLOps and LLMOps: data quality reports and traces."

5. Show `/agent/analyze`.
Say: "The agent is controlled. It routes the question to the right business tool instead of improvising."

## 5-Minute Demo

1. Start with the business problem.
Say: "Risk signals live across customer exports, documents and support history."

2. Show architecture image or Mermaid.
Say: "The stack uses Streamlit, FastAPI, PostgreSQL, pgvector, XGBoost, LangGraph, Airflow, dbt and monitoring."

3. Show customer import and risk endpoints in Swagger.
Say: "The system can ingest customer data and score churn risk."

4. Show `CUST-001` analysis.
Say: "The model output is converted into a business risk score, reasons and recommended actions."

5. Show weekly report.
Say: "Managers get a weekly operational view, not only raw predictions."

6. Show RAG endpoints.
Say: "Documents can be uploaded, chunked, embedded and queried with source traceability."

7. Show Airflow.
Say: "The pipeline can be scheduled and repeated."

8. Show monitoring.
Say: "The project includes readiness checks, ML monitoring reports and LLM traces."

9. Close with limits.
Say: "This is a local portfolio release. Next steps would be AWS deployment, auth and stronger evaluation."

## Screens To Show

- Streamlit dashboard
- FastAPI `/docs`
- `/health` and `/ready`
- `/risk/priority-customers`
- `/reports/weekly-risk`
- `/agent/analyze`
- ML monitoring HTML report
- Airflow DAG page

## Endpoints To Show

- `GET /health`
- `GET /ready`
- `GET /customers`
- `POST /risk/analyze-customer`
- `GET /risk/priority-customers`
- `GET /reports/weekly-risk`
- `POST /agent/analyze`
- `GET /monitoring/llm/summary`
- `GET /monitoring/ml/report?format=html`

## Errors To Avoid

- Do not demo RAG generation without an OpenAI API key.
- Do not start recording before `scripts/dev/demo-seed.ps1` finishes.
- Do not show `.env`.
- Do not claim this is production cloud infrastructure.
- Do not overstate the sample ML dataset.
