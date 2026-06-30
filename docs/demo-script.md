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

1. Show Executive Overview.
Say: "This is AI RiskOps Copilot, a local AI product for customer risk operations."

2. Show KPI cards and Top Priority Customers.
Say: "The system combines structured customer data and a churn model to prioritize accounts."

3. Show Action Plan.
Say: "The interface turns risk scores and document evidence into concrete business actions."

4. Open Client Risk and analyze `CUST-001`.
Say: "A manager can inspect one customer, see the risk drivers, document evidence, owner and recommended next step."

5. Open AI Assistant and ask: `Which customers are high risk this week?`
Say: "The agent is controlled. It routes the question to the right business tool instead of improvising."

Close with:
"The rest of the app shows document RAG, Airflow/dbt data engineering and monitoring, so the project is more than a chatbot demo."

## 5-Minute Demo

1. Start with the business problem.
Say: "Risk signals live across customer exports, documents and support history."

2. Show architecture image or Mermaid.
Say: "The stack uses Streamlit, FastAPI, PostgreSQL, pgvector, XGBoost, LangGraph, Airflow, dbt and monitoring."

3. Show Executive Overview.
Say: "The main page is designed for managers: KPIs, priority customers, weekly summary and action plan."

4. Show Client Risk and analyze `CUST-001`.
Say: "The model output is converted into a business risk score, reasons, document risk evidence and recommended actions."

5. Show Client 360 and Customer Risk History.
Say: "The Client 360 section brings customer profile, risk explanation, document evidence, actions and history into one view."

6. Show AI Assistant.
Say: "The agent routes questions to known tools: priority customers, weekly report, customer analysis or RAG."

7. Show Documents and RAG.
Say: "Documents can be uploaded, processed, embedded and queried with source traceability. Document risk uses simple keyword extraction and does not require OpenAI."

8. Show Data Pipeline.
Say: "Airflow orchestrates the workflow. dbt transforms PostgreSQL data into analytics-ready tables."

9. Show Monitoring.
Say: "The project includes readiness checks, ML monitoring reports and LLM traces."

10. Show About Project.
Say: "This page summarizes the business value, stack, limitations and next improvements for an interview."

11. Close with limits.
Say: "This is a local portfolio release. Next steps would be AWS deployment, auth and stronger evaluation."

## Screens To Show

- Streamlit Executive Overview
- Streamlit Client Risk
- Streamlit AI Assistant
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
- `GET /risk/document-risk/CUST-001`
- `GET /risk/client-360/CUST-001`
- `GET /risk/action-plan`
- `GET /risk/priority-customers`
- `GET /reports/weekly-risk`
- `POST /agent/analyze`
- `GET /monitoring/llm/summary`
- `GET /monitoring/ml/report?format=html`

## Final UI Demo Order

1. Executive Overview
2. Client Risk
3. AI Assistant
4. Documents and RAG
5. Data Pipeline
6. Monitoring
7. About Project

## Phrases To Say By Page

- Executive Overview: "This is the manager view: KPIs, top risky customers and the action plan."
- Client Risk: "This page explains one customer's score, document evidence, reasons and recommended actions."
- AI Assistant: "The agent is controlled and routes questions to known tools."
- Documents and RAG: "This page adds document intelligence with source traceability."
- Data Pipeline: "Airflow orchestrates and dbt transforms the data."
- Monitoring: "This page shows health, readiness, ML report status and LLM traces."
- About Project: "This is the recruiter summary of what the project demonstrates."

## Errors To Avoid

- Do not demo RAG generation without an OpenAI API key.
- Do not start recording before `scripts/dev/demo-seed.ps1` finishes.
- Do not show `.env`.
- Do not claim this is production cloud infrastructure.
- Do not overstate the sample ML dataset.

## Document Risk Demo File

Use a non-sensitive test file containing:

`Customer CUST-001 has two unpaid invoices, repeated support escalations and a contract penalty for late payment.`

Upload it as a small CSV or PDF, process it, then show `/risk/document-risk/CUST-001` and the Client Risk page.
