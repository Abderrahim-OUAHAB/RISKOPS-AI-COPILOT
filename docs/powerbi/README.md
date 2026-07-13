# AI RiskOps Executive Dashboard

The AI RiskOps Executive Dashboard is a Power BI portfolio dashboard for the AI RiskOps Copilot project. It turns the FastAPI risk and action endpoints into an executive reporting layer for customer risk operations.

## Why It Matters

The dashboard shows that AI RiskOps Copilot is not only an AI backend and Streamlit app. It also supports business intelligence workflows for managers who need a familiar executive reporting surface.

## Data Sources

Power BI Desktop connects to the local FastAPI backend:

- `http://localhost:8000/risk/priority-customers`
- `http://localhost:8000/actions/board`

Power BI Desktop connects to `localhost` because it runs on the host machine.

## Local Prerequisites

- Docker Desktop running.
- AI RiskOps backend available locally.
- Power BI Desktop installed.
- The PBIX file from this folder.

## Open The Dashboard

1. Start the backend with Docker Compose.
2. Confirm FastAPI is available at `http://localhost:8000/docs`.
3. Open `docs/powerbi/AI-RiskOps-Executive-Dashboard.pbix` in Power BI Desktop.
4. Click **Refresh**.

## Dashboard Pages

1. Executive Overview
2. Customer Risk Analysis
3. Action Board Operations
4. Risk Drivers
5. AI Monitoring

Hidden or interactive pages:

- Customer Tooltip
- Client 360 drill-through page

## Main KPIs

- Total Customers
- High Risk Customers
- Medium Risk Customers
- Low Risk Customers
- Average Risk Score
- Average Confidence
- Total Actions
- Open Actions
- High Priority Actions
- Overdue Actions
- RiskOps Pressure Score
- Customers Above Threshold

## Interactions

- Risk level slicers are synced across pages.
- Reset filters bookmarks are available.
- A what-if parameter controls the risk score threshold.
- Customer tooltip provides quick contextual detail.
- Client 360 drill-through supports customer-level investigation.
- Mobile layouts are configured for main pages.

## Privacy And Anonymization

The dashboard uses privacy-safe customer aliases for display. Documentation should avoid exposing internal customer IDs or non-anonymized customer references.

## Power BI Service Limitations

Power BI Service cannot refresh `localhost` endpoints directly without additional infrastructure. Automatic refresh requires either:

- an on-premises data gateway for localhost access, or
- a deployed public or internal API endpoint.

## Included Assets

- `AI-RiskOps-Executive-Dashboard.pbix`
- `AI-RiskOps-Executive-Dashboard.pdf`
- `riskops-enterprise-theme.json`
- `performance/powerbi-performance-analyzer.json`

## Portfolio Value

This dashboard demonstrates executive BI, API-based data loading, operational action tracking, dashboard UX, drill-through analysis, Power BI theming, mobile layout work and performance review.
