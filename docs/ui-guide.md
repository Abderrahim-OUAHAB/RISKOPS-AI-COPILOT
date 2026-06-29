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
4. Show Today's Action Plan to prove the system gives business actions, not only scores.
5. Open Client Risk.
6. Analyze `CUST-001` and review the score bar, reasons, recommended actions and prediction history.
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
- `GET /risk/history?customer_id=...`

The page displays a risk score bar, risk badge, churn probability, reasons, recommended actions, prediction id, prediction history and technical details.

### AI Assistant

This page wraps the controlled LangGraph agent in a business interface.

It uses:

- `POST /agent/analyze`

The page includes quick questions, a question input, an answer card, selected tool badge, source preview, data summary and hidden technical details.
