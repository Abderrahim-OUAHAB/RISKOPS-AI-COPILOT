# Final Product UI Guide

## Objective

The Streamlit interface is the final product shell for AI RiskOps Copilot. It is designed for a manager or recruiter who needs to understand the system quickly without reading API payloads.

The UI focuses on:

- customer risk visibility,
- recommended actions,
- platform readiness,
- controlled AI assistant usage,
- document risk, Client 360, action plan, pipeline and monitoring access.

## Final Navigation

The sidebar exposes seven pages:

- Executive Overview
- Client Risk
- Documents and RAG
- AI Assistant
- Data Pipeline
- Monitoring
- About Project

The active page is selected through the sidebar navigation. Each page keeps one clear job and avoids long technical text.

The sidebar also shows:

- Local Docker Environment
- API status
- FastAPI Docs link
- Streamlit link
- Airflow link
- ML Report link

## Colors

Official UI palette:

- High risk: `#DC2626`
- Medium risk: `#F59E0B`
- Low risk: `#16A34A`
- Healthy: `#16A34A`
- Warning: `#F59E0B`
- Error: `#DC2626`
- Primary blue: `#2563EB`
- Dark text: `#111827`
- Light background: `#F3F4F6`
- Card background: `#FFFFFF`
- Border: `#E5E7EB`

## UI Components

Reusable components live in `frontend/components.py`:

- `inject_global_css()`
- `risk_color(level)`
- `risk_badge(level)`
- `status_badge(status)`
- `metric_card(title, value, subtitle, color)`
- `section_header(title, subtitle)`
- `render_empty_state(message)`
- `render_error(message)`
- `render_success(message)`
- `render_warning(message)`
- `render_risk_score(score, level)`
- `format_list_items(items)`
- `safe_json_preview(data)`

API calls are centralized in `frontend/api_client.py`.

## UX Rules

- The interface supports English and French from the sidebar language selector.
- JSON is not shown by default.
- Technical payloads are placed inside `Technical details` expanders.
- Error messages are short and user-readable.
- KPI cards summarize state before tables.
- Risk badges use the official color palette.
- RAG processing includes a cost reminder because embeddings use the OpenAI API.
- Executive Overview is the main demo page.
- Client Risk is focused on one customer analysis at a time.
- AI Assistant shows controlled agent routing, not an uncontrolled chatbot.

## Managed Errors

The API client handles:

- backend unavailable,
- request timeout,
- `400` invalid request,
- `404` missing resource,
- `503` service not ready,
- `500` backend error.

Streamlit does not display Python stack traces for API failures.

## Recommended Demo Order

1. Open Executive Overview.
2. Explain the KPI cards: total customers, risk levels, recommended actions and system status.
3. Show Top Priority Customers and the reason/action cards.
4. Show Action Plan to prove the system gives business actions, not only scores.
5. Open Client Risk.
6. Analyze `CUST-001` and review the score bar, document risk, evidence, Client 360 summary, recommended actions and prediction history.
7. Open AI Assistant.
8. Ask: `Which customers are high risk this week?`
9. Ask: `What actions should I take today?`
10. Keep Documents and RAG, Data Pipeline and Monitoring as supporting pages for the longer demo.

## Business Pages

### Executive Overview

This is the landing page for a portfolio demo. It uses:

- `GET /customers`
- `GET /risk/priority-customers`
- `GET /reports/weekly-risk`
- `GET /health`
- `GET /ready`

It displays KPI cards, an executive summary, top priority customers, main risk drivers, Today's Action Plan and hidden technical details.

### Client Risk

This page supports one-customer analysis. The user can select an imported customer or enter a `customer_id` manually.

It uses:

- `GET /customers`
- `POST /risk/analyze-customer`
- `GET /risk/document-risk/{customer_id}`
- `GET /risk/client-360/{customer_id}`
- `GET /risk/history?customer_id=...`

The page displays a risk score bar, risk badge, churn probability, score breakdown, document risk score, document signals, linked documents, evidence previews, Client 360 summary, ownership, recommended actions, prediction history and technical details.

### Action Plan

Executive Overview calls `GET /risk/action-plan` and displays the top 3 to 5 actions with customer, priority, action label, owner, due date and reason.

### Document Risk Demo

Upload and process a CSV or PDF containing a customer id such as `CUST-001` and risk language such as `unpaid invoice`, `support escalation` or `contract penalty`. The app links the document to the customer when the id appears in the filename or processed chunks.

### AI Assistant

This page wraps the controlled LangGraph agent in a business interface.

It uses:

- `POST /agent/analyze`

The page includes quick questions, a question input, an answer card, selected tool badge, source preview, data summary and hidden technical details.

### Documents and RAG

This page supports document intelligence for PDF and CSV files.

It uses:

- `GET /documents`
- `POST /documents/upload`
- `POST /documents/{document_id}/process`
- `POST /rag/ask`

It displays upload controls, document status, processing action, RAG answer card, source expanders and hidden technical details.

If OpenAI is not configured, the user-facing message is:

`RAG requires OPENAI_API_KEY for embeddings and generation.`

### Data Pipeline

This page explains the data engineering layer.

It shows:

- Airflow URL
- DAG name: `riskops_daily_pipeline`
- backend health
- weekly report summary
- pipeline tasks
- data flow from CSV to weekly risk report

Pipeline flow:

`Customers CSV -> PostgreSQL -> dbt transformations -> XGBoost training -> Weekly risk report`

### Monitoring

This page shows operational status.

It uses:

- `GET /health`
- `GET /ready`
- `GET /monitoring/llm/summary`
- `GET /monitoring/llm/traces`
- `POST /monitoring/ml/generate-report`
- `GET /monitoring/ml/report`

It displays API health, readiness, LLM trace summary, ML report status, recent traces, report generation and hidden technical details.

### About Project

This page is an interview aid. It summarizes:

- Business Problem
- Solution
- Architecture Summary
- Main Features
- Technology Stack
- What This Project Demonstrates
- Current Limitations
- Next Improvements

## Screenshots

Add real screenshots under `docs/screenshots/` before publishing:

- `screenshot-executive-overview.png`
- `screenshot-client-risk.png`
- `screenshot-ai-assistant.png`
- `screenshot-documents-rag.png`
- `screenshot-data-pipeline.png`
- `screenshot-monitoring.png`
- `screenshot-airflow-dag.png`
