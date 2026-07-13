# Power BI Dashboard Specification

## Dashboard Overview

`AI RiskOps Executive Dashboard` is an executive Power BI layer for AI RiskOps Copilot. It connects to the local FastAPI backend and visualizes customer risk, action operations, risk drivers and AI monitoring.

## Data Sources

- FastAPI priority customers endpoint.
- FastAPI Action Board endpoint.

Local source URLs:

- `http://localhost:8000/risk/priority-customers`
- `http://localhost:8000/actions/board`

## Tables

- `Risk_Customers`: customer-level risk metrics and aliases.
- `Action_Board`: action workflow data, status, priority, owner and due dates.
- `Risk_Drivers`: normalized risk reason or driver records.
- `_Measures`: DAX measures used by the report pages.

## Relationships

- `Risk_Customers[customer_id]` to `Action_Board[customer_id]`.
- `Risk_Customers[Customer Alias]` to `Risk_Drivers[Customer Alias]`, if present in the PBIX/model.

## Calculated Columns

- Customer Alias
- Due Date Display
- Confidence Band
- Risk Level Bg Color
- Action Alias
- Action Due Date Display
- Action Customer Alias
- Priority Bg Color
- Status Bg Color
- Driver Risk Level Bg Color

## Measures

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
- Low Confidence Customers
- Confidence Coverage
- Selected Risk Threshold
- Customers Above Threshold
- Customers Above Threshold %

## Pages And Visuals

### Executive Overview

- Executive KPI cards.
- Risk distribution donut chart.
- Top risk customers table.
- Summary action indicators.

### Customer Risk Analysis

- Customer risk score analysis.
- Scatter plot for risk score versus confidence.
- Risk level and confidence context.

### Action Board Operations

- Actions by priority, status and owner.
- Operational follow-up view for open and overdue work.

### Risk Drivers

- Risk driver frequency analysis.
- Driver-level segmentation by risk level.

### AI Monitoring

- AI and workflow monitoring view.
- Operational health and quality signals.

## Bookmarks

Reset filters bookmarks are included for dashboard usability and portfolio demonstration.

## Tooltip

The Customer Tooltip page provides contextual customer detail without exposing internal customer IDs in the visible report layer.

## Drill-Through

The Client 360 drill-through page supports investigation of one selected customer alias and related risk/action context.

## Mobile Layout

Mobile layouts are configured for the main report pages to support portfolio screenshots and executive review on smaller screens.

## Performance Analyzer Notes

The exported Performance Analyzer data is stored in `docs/powerbi/performance/powerbi-performance-analyzer.json`. Use it to review visual query timing and identify slow visuals before publishing.

## Security And Privacy Notes

- Use customer aliases in visuals and documentation.
- Avoid exposing internal customer IDs in screenshots or portfolio materials.
- Do not store API credentials in PBIX metadata or committed files.
- Keep local FastAPI endpoints for portfolio use unless a secure deployed API is available.
