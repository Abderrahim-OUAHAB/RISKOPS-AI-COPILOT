# Final Product UI Guide

## Objective

The Streamlit interface is the product shell for AI RiskOps Copilot. It is designed for a manager or recruiter who needs to understand the system quickly without reading API payloads.

The UI focuses on:

- customer risk visibility,
- recommended actions,
- platform readiness,
- controlled AI assistant usage,
- document, pipeline and monitoring access.

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

- The interface language is English.
- JSON is not shown by default.
- Technical payloads are placed inside `Technical details` expanders.
- Error messages are short and user-readable.
- KPI cards summarize state before tables.
- Risk badges use the official color palette.
- RAG processing includes a cost reminder because embeddings use the OpenAI API.

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
2. Import `data/sample/customers_sample.csv` in Client Risk.
3. Analyze `CUST-001` and review the risk score and actions.
4. Ask the AI Assistant: `Which customers are at risk this week?`
5. Upload `data/sample/rag_demo_customer_risks.csv` in Documents and RAG.
6. Process the document once.
7. Ask: `Which customers are high risk and what actions are recommended?`
8. Open Monitoring.
9. Generate the ML monitoring report.
10. Open the HTML report link.
