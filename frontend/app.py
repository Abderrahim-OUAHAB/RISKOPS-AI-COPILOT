import html
from typing import Any

import pandas as pd
import streamlit as st

from api_client import (
    API_BASE_URL,
    get_customers,
    get_documents,
    get_health,
    get_llm_summary,
    get_llm_traces,
    get_ml_report_status,
    get_priority_customers,
    get_ready,
    get_risk_history,
    get_weekly_report,
    safe_post,
)
from components import (
    format_list_items,
    inject_global_css,
    metric_card,
    render_empty_state,
    render_error,
    render_risk_score,
    render_success,
    render_warning,
    risk_badge,
    risk_color,
    safe_json_preview,
    section_header,
    status_badge,
)


PAGES = [
    "Executive Overview",
    "Client Risk",
    "Documents and RAG",
    "AI Assistant",
    "Data Pipeline",
    "Monitoring",
    "About Project",
]


st.set_page_config(
    page_title="AI RiskOps Copilot",
    page_icon="",
    layout="wide",
)
inject_global_css()


def render_product_header() -> None:
    st.markdown(
        """
        <div class="riskops-product-header">
            <h1>AI RiskOps Copilot</h1>
            <p>Business risk intelligence powered by AI, data pipelines and monitoring.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> str:
    with st.sidebar:
        st.markdown("## AI RiskOps Copilot")
        st.caption("Portfolio V1 interface")

        page = st.radio("Navigation", PAGES, label_visibility="collapsed")

        st.divider()
        st.markdown("### System status")
        health = get_health()
        if health.ok:
            st.markdown(status_badge("healthy"), unsafe_allow_html=True)
        else:
            st.markdown(status_badge("unavailable"), unsafe_allow_html=True)
            st.caption(health.error)

        st.divider()
        st.markdown("### Useful links")
        st.link_button("FastAPI Docs", "http://localhost:8000/docs", use_container_width=True)
        st.link_button("Airflow", "http://localhost:8080", use_container_width=True)
        st.link_button(
            "ML Report",
            "http://localhost:8000/monitoring/ml/report?format=html",
            use_container_width=True,
        )
        st.caption(f"API: {API_BASE_URL}")

    return page


def _customers() -> list[dict]:
    result = get_customers()
    if not result.ok:
        render_warning(f"Customers unavailable: {result.error}")
        return []
    return result.data or []


def _customer_options(customers: list[dict]) -> dict[str, str]:
    return {
        f"{customer.get('customer_external_id')} - {customer.get('name') or 'Unnamed customer'}": customer.get(
            "customer_external_id"
        )
        for customer in customers
        if customer.get("customer_external_id")
    }


def _risk_table(customers: list[dict]) -> None:
    if not customers:
        render_empty_state("Import customer data to populate this view.")
        return

    rows = [
        {
            "Customer": customer.get("customer_id") or customer.get("customer_external_id"),
            "Name": customer.get("name"),
            "Risk score": customer.get("risk_score"),
            "Risk level": customer.get("risk_level"),
            "Support tickets": customer.get("support_tickets"),
            "Late payments": customer.get("late_payments"),
        }
        for customer in customers
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_percent(value: Any) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "-"


def _customer_name(customer: dict) -> str:
    return str(customer.get("name") or "Unnamed customer")


def _customer_external_id(customer: dict) -> str:
    return str(customer.get("customer_id") or customer.get("customer_external_id") or "")


def _dedupe(items: list[str], limit: int | None = None) -> list[str]:
    seen = set()
    output = []
    for item in items:
        clean_item = str(item).strip()
        if not clean_item or clean_item.lower() in seen:
            continue
        seen.add(clean_item.lower())
        output.append(clean_item)
        if limit is not None and len(output) >= limit:
            break
    return output


def _recommended_actions(priority_rows: list[dict], weekly_report: dict, limit: int = 5) -> list[str]:
    actions: list[str] = []
    for customer in priority_rows:
        if str(customer.get("risk_level", "")).lower() == "high":
            actions.extend(customer.get("recommended_actions") or [])
    actions.extend(weekly_report.get("recommended_actions") or [])
    fallback_actions = [
        "Contact high-risk customers within 48 hours",
        "Review late payments",
        "Escalate repeated support issues",
        "Prepare retention offer",
        "Monitor medium-risk customers this week",
    ]
    return _dedupe(actions + fallback_actions, limit=limit)


def _main_risk_drivers(priority_rows: list[dict]) -> list[str]:
    reasons: list[str] = []
    for customer in priority_rows:
        reasons.extend(customer.get("top_reasons") or [])
    if not reasons:
        return ["Late payments", "Repeated support tickets", "High churn probability"]
    return _dedupe(reasons, limit=4)


def _business_summary(customers: list[dict], priority_rows: list[dict], weekly_report: dict) -> str:
    total_attention = _as_int(weekly_report.get("high_risk_customers")) + _as_int(
        weekly_report.get("medium_risk_customers")
    )
    if not total_attention and priority_rows:
        total_attention = len(priority_rows)
    total_customers = _as_int(weekly_report.get("total_customers"), len(customers))
    drivers = ", ".join(driver.lower() for driver in _main_risk_drivers(priority_rows)[:3])
    if total_customers == 0:
        return "No customers found. Run the demo seed script or import a CSV file."
    return (
        f"{total_attention} customers require attention this week. "
        f"The main drivers are {drivers}."
    )


def _render_insight(title: str, body: str, color: str = "#2563EB") -> None:
    st.markdown(
        f"""
        <div class="riskops-insight-box" style="border-left-color:{html.escape(color)};">
            <div class="riskops-insight-title">{html.escape(title)}</div>
            <div class="riskops-insight-body">{html.escape(body)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_action_checklist(actions: list[str]) -> None:
    if not actions:
        render_empty_state("No recommended actions available yet.")
        return
    items = "".join(
        f'<li><span class="riskops-check">&#10003;</span>{html.escape(action)}</li>'
        for action in actions
    )
    st.markdown(f'<ul class="riskops-checklist">{items}</ul>', unsafe_allow_html=True)


def _render_priority_customer_cards(priority_rows: list[dict]) -> None:
    if not priority_rows:
        render_empty_state("No priority customers available yet.")
        return

    for customer in priority_rows[:5]:
        score = _as_int(customer.get("risk_score"))
        level = customer.get("risk_level")
        name = _customer_name(customer)
        customer_id = _customer_external_id(customer)
        reasons = format_list_items(customer.get("top_reasons") or [])
        actions = format_list_items(customer.get("recommended_actions") or [])
        st.markdown(
            f"""
            <div class="riskops-customer-card">
                <div class="riskops-customer-header">
                    <div>
                        <div class="riskops-customer-name">{html.escape(name)}</div>
                        <div class="riskops-customer-meta">{html.escape(customer_id)}</div>
                    </div>
                    <div>{risk_badge(level)}</div>
                </div>
                <div class="riskops-score-label">
                    <span>Risk score</span>
                    <span>{score}/100</span>
                </div>
                <div class="riskops-score-track">
                    <div class="riskops-score-fill" style="width:{max(0, min(100, score))}%;background:{risk_color(level)};"></div>
                </div>
                <div style="height:0.85rem;"></div>
                <strong>Top reasons</strong>
                {reasons}
                <strong>Recommended actions</strong>
                {actions}
            </div>
            """,
            unsafe_allow_html=True,
        )


def _find_customer(customers: list[dict], customer_id: str) -> dict:
    normalized = customer_id.strip().lower()
    for customer in customers:
        if str(customer.get("customer_external_id", "")).lower() == normalized:
            return customer
    return {}


def _render_history(history: list[dict]) -> None:
    if not history:
        render_empty_state("No prediction history yet.")
        return
    rows = [
        {
            "Date": item.get("created_at"),
            "Score": item.get("risk_score"),
            "Level": item.get("risk_level"),
            "Top reasons": ", ".join((item.get("reasons") or [])[:2]),
        }
        for item in history
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_executive_overview() -> None:
    section_header(
        "Executive Overview",
        "See where customer risk is concentrated and what the team should do next.",
    )

    if st.button("Refresh overview", use_container_width=False):
        st.rerun()

    with st.spinner("Loading executive risk overview..."):
        customers_result = get_customers()
        priority = get_priority_customers()
        weekly = get_weekly_report()
        health = get_health()
        ready = get_ready()
        llm_summary = get_llm_summary()

    customers = customers_result.data if customers_result.ok and customers_result.data else []
    priority_rows = priority.data if priority.ok and priority.data else []
    report = weekly.data if weekly.ok and weekly.data else {}
    actions = _recommended_actions(priority_rows, report)
    ready_label = "Ready" if ready.ok else "Not ready"

    if not customers_result.ok:
        render_error("The backend is not available. Start Docker services and refresh.")
    elif not customers:
        render_warning("No customers found. Run the demo seed script or import a CSV file.")

    _render_insight(
        "Executive Summary",
        _business_summary(customers, priority_rows, report),
        "#2563EB",
    )

    cols = st.columns(6)
    with cols[0]:
        metric_card("Total Customers", report.get("total_customers", len(customers)), "Portfolio size", "#2563EB")
    with cols[1]:
        metric_card("High Risk Customers", report.get("high_risk_customers", "-"), "Immediate attention", "#DC2626")
    with cols[2]:
        metric_card("Medium Risk Customers", report.get("medium_risk_customers", "-"), "Watch this week", "#F59E0B")
    with cols[3]:
        metric_card("Low Risk Customers", report.get("low_risk_customers", "-"), "Stable accounts", "#16A34A")
    with cols[4]:
        metric_card("Recommended Actions", len(actions), "Prioritized next steps", "#2563EB")
    with cols[5]:
        metric_card("System Status", ready_label, "Local Docker Environment", risk_color("low" if ready.ok else "high"))

    section_header("Top Priority Customers", "Customers ranked by risk score and recommended next action.")
    if priority_rows:
        _render_priority_customer_cards(priority_rows)
    elif not priority.ok:
        render_warning(f"Priority customers unavailable: {priority.error}")
    else:
        render_empty_state("No priority customers available yet.")

    col1, col2 = st.columns([1, 1])
    with col1:
        section_header("Weekly Risk Summary", "Short operational summary for managers.")
        if report.get("executive_summary"):
            _render_insight("Business impact", report["executive_summary"], "#F59E0B")
        elif weekly.ok:
            render_empty_state("Weekly report is empty.")
        else:
            render_warning(f"Weekly report unavailable: {weekly.error}")

        _render_insight(
            "Main risk drivers",
            "; ".join(_main_risk_drivers(priority_rows)),
            "#DC2626" if priority_rows else "#F59E0B",
        )

    with col2:
        section_header("Today's Action Plan", "Recommended next step for the risk team.")
        _render_action_checklist(actions)

    if not ready.ok:
        render_warning("The churn model is not trained yet. Run the training pipeline." if ready.status_code == 503 else ready.error or "System is not ready.")

    with st.expander("Technical details"):
        safe_json_preview(
            {
                "customers_status": customers_result.status_code,
                "health_status": health.status_code,
                "weekly_report": report,
                "readiness_status": ready.status_code,
                "llm_summary": llm_summary.data if llm_summary.ok else llm_summary.error,
            }
        )


def render_client_risk() -> None:
    section_header(
        "Client Risk",
        "Analyze one customer, understand the risk drivers and review the recommended actions.",
    )

    if st.button("Refresh client data"):
        st.rerun()

    customer_file = st.file_uploader("Import customer CSV", type=["csv"], accept_multiple_files=False)
    if customer_file and st.button("Import customers", type="primary"):
        with st.spinner("Importing customer CSV..."):
            files = {
                "file": (
                    customer_file.name,
                    customer_file.getvalue(),
                    customer_file.type or "text/csv",
                )
            }
            result = safe_post("/customers/import", files=files, timeout=30)
        if result.ok:
            render_success(f"{result.data.get('imported_count', 0)} customers imported.")
        else:
            render_error(f"Customer import failed: {result.error}")

    with st.spinner("Loading customer portfolio..."):
        customers = _customers()

    if not customers:
        render_empty_state("No customers found. Run the demo seed script or import a CSV file.")
        return

    section_header("Customer Selection", "Choose from the imported portfolio or enter an ID manually.")
    options = _customer_options(customers)
    selected_label = st.selectbox("Select customer", list(options.keys()))
    default_customer_id = options[selected_label]
    manual_customer_id = st.text_input("Or enter customer_id manually", value=default_customer_id)
    selected_customer_id = manual_customer_id.strip() or default_customer_id
    selected_customer = _find_customer(customers, selected_customer_id)

    if selected_customer:
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Customer", selected_customer_id)
        col_b.metric("Name", _customer_name(selected_customer))
        col_c.metric("Contract", selected_customer.get("contract_type") or "-")

    if st.button("Analyze Customer", use_container_width=True, type="primary"):
        with st.spinner("Analyzing customer risk..."):
            result = safe_post("/risk/analyze-customer", json={"customer_id": selected_customer_id}, timeout=60)

        if result.ok:
            analysis = result.data
            section_header("Customer Risk Profile", "Score, level, churn probability and business explanation.")
            card_cols = st.columns([1.1, 1])
            with card_cols[0]:
                render_risk_score(analysis.get("risk_score"), analysis.get("risk_level"))
            with card_cols[1]:
                st.markdown(
                    f"""
                    <div class="riskops-soft-box">
                        <div class="riskops-card-title">Customer</div>
                        <div class="riskops-card-value">{html.escape(str(analysis.get("customer_id") or selected_customer_id))}</div>
                        <div class="riskops-card-subtitle">{html.escape(_customer_name(selected_customer) if selected_customer else "Customer record")}</div>
                        <div style="height:0.75rem;"></div>
                        <div>{risk_badge(analysis.get("risk_level"))}</div>
                        <p><strong>Churn probability:</strong> {_as_percent(analysis.get("churn_probability"))}</p>
                        <p><strong>Prediction ID:</strong> {html.escape(str(analysis.get("prediction_id", "-")))}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            col1, col2 = st.columns([1, 1])
            with col1:
                _render_insight("Main risk drivers", "The analysis explains why this customer needs attention.", "#DC2626")
                st.markdown(format_list_items(analysis.get("reasons")), unsafe_allow_html=True)
            with col2:
                _render_insight("Recommended next step", "Turn the score into concrete customer operations.", "#2563EB")
                _render_action_checklist(analysis.get("recommended_actions") or [])

            with st.expander("Technical details"):
                safe_json_preview(analysis)

            with st.spinner("Loading risk history..."):
                history = get_risk_history(selected_customer_id)
            section_header("Customer Risk History", "Recent predictions saved for this customer.")
            if history.ok:
                _render_history(history.data or [])
            else:
                render_warning(f"Prediction history unavailable: {history.error}")
        else:
            if result.status_code == 503:
                render_error("The churn model is not trained yet. Run the training pipeline.")
            elif result.status_code == 404:
                render_error("The requested customer was not found.")
            else:
                render_error(f"RiskOps analysis failed: {result.error}")

    with st.expander("Customer portfolio"):
        _risk_table(customers)


def render_documents_rag() -> None:
    section_header(
        "Documents and RAG",
        "Upload PDF or CSV files, process them and ask focused questions with sources.",
    )

    uploaded_files = st.file_uploader(
        "Upload PDF or CSV files",
        type=["pdf", "csv"],
        accept_multiple_files=True,
    )

    if uploaded_files and st.button("Upload selected files", type="primary"):
        for uploaded_file in uploaded_files:
            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type or "application/octet-stream",
                )
            }
            result = safe_post("/documents/upload", files=files, timeout=30)
            if result.ok:
                render_success(f"{result.data.get('filename')} uploaded with document id {result.data.get('id')}.")
            else:
                render_error(f"Upload failed for {uploaded_file.name}: {result.error}")

    documents_result = get_documents()
    if not documents_result.ok:
        render_warning(f"Document list unavailable: {documents_result.error}")
        return

    documents = documents_result.data or []
    if not documents:
        render_empty_state("No documents uploaded yet.")
        return

    rows = [
        {
            "ID": document.get("id"),
            "Filename": document.get("filename"),
            "Type": document.get("document_type"),
            "Status": document.get("status"),
            "Processed at": document.get("processed_at"),
        }
        for document in documents
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    options = {
        f"{document.get('id')} - {document.get('filename')} ({document.get('status')})": document.get("id")
        for document in documents
    }
    selected_label = st.selectbox("Document", list(options.keys()))
    selected_document_id = options[selected_label]

    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("Process selected document", use_container_width=True):
            result = safe_post(f"/documents/{selected_document_id}/process", timeout=120)
            if result.ok:
                render_success(
                    f"Document {result.data.get('document_id')} processed: {result.data.get('chunks_created')} chunks created."
                )
            else:
                render_error(f"Processing failed: {result.error}")

    with col2:
        st.caption("Processing creates embeddings. Use small demo files to control OpenAI API cost.")

    with st.form("rag-question-form"):
        question = st.text_input(
            "Question",
            value="Which customers are high risk and what actions are recommended?",
        )
        ask_submitted = st.form_submit_button("Ask Copilot")

    if ask_submitted:
        result = safe_post(
            "/rag/ask",
            json={"question": question, "document_id": selected_document_id},
            timeout=120,
        )
        if result.ok:
            st.markdown("#### Answer")
            st.write(result.data.get("answer"))
            sources = result.data.get("sources") or []
            if sources:
                st.markdown("#### Sources")
                for source in sources:
                    with st.expander(
                        f"Document {source.get('document_id')} - chunk {source.get('chunk_id')} - score {source.get('similarity_score')}"
                    ):
                        st.write(source.get("content_preview"))
        else:
            render_error(f"RAG request failed: {result.error}")


def render_ai_assistant() -> None:
    section_header(
        "Ask the AI RiskOps Agent",
        "Ask a business question. The controlled agent chooses the right risk, report or document tool.",
    )

    if "agent_question" not in st.session_state:
        st.session_state.agent_question = "Which customers are high risk this week?"

    quick_questions = [
        "Which customers are high risk this week?",
        "Generate a weekly risk summary",
        "Analyze customer CUST-001",
        "What actions should I take today?",
    ]

    st.markdown("#### Quick questions")
    quick_cols = st.columns(4)
    for index, question in enumerate(quick_questions):
        if quick_cols[index].button(question, use_container_width=True):
            st.session_state.agent_question = question
            st.rerun()

    if st.button("Clear question"):
        st.session_state.agent_question = ""
        st.rerun()

    with st.form("riskops-agent-form"):
        question = st.text_input("Question", key="agent_question")
        submitted = st.form_submit_button("Ask Agent", type="primary")

    if submitted:
        if not question.strip():
            render_warning("Enter a question before asking the agent.")
            return

        with st.spinner("Running RiskOps agent workflow..."):
            result = safe_post("/agent/analyze", json={"question": question}, timeout=60)

        if result.ok:
            data = result.data or {}
            st.markdown("#### Answer")
            st.markdown(
                f"""
                <div class="riskops-insight-box" style="border-left-color:#2563EB;">
                    <div class="riskops-insight-title">Agent response</div>
                    <div class="riskops-insight-body">{html.escape(str(data.get("answer") or "No answer returned."))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(status_badge(data.get("selected_tool") or "agent_tool"), unsafe_allow_html=True)

            sources = data.get("sources") or []
            if sources:
                st.markdown("#### Sources")
                for source in sources:
                    with st.expander(f"Source {source.get('chunk_id', '')}".strip()):
                        st.write(source.get("content_preview") or source)

            summary_data = data.get("data") or {}
            if isinstance(summary_data, dict) and summary_data:
                st.markdown("#### Data summary")
                summary_items = []
                for key, value in list(summary_data.items())[:5]:
                    if isinstance(value, (str, int, float, bool)) or value is None:
                        summary_items.append(f"{key}: {value}")
                    elif isinstance(value, list):
                        summary_items.append(f"{key}: {len(value)} items")
                    else:
                        summary_items.append(f"{key}: available")
                st.markdown(format_list_items(summary_items), unsafe_allow_html=True)

            with st.expander("Technical details"):
                safe_json_preview(data)
        else:
            render_error(f"Agent failed: {result.error}")


def render_data_pipeline() -> None:
    section_header(
        "Data Pipeline",
        "Local orchestration for API checks, customer ingestion, dbt models, ML training and reports.",
    )

    ready = get_ready()
    weekly = get_weekly_report()
    cols = st.columns(3)
    with cols[0]:
        metric_card("Backend", "Ready" if ready.ok else "Not ready", ready.error or "FastAPI readiness", risk_color("low" if ready.ok else "high"))
    with cols[1]:
        metric_card("Airflow", "Local UI", "http://localhost:8080", "#2563EB")
    with cols[2]:
        metric_card("dbt", "SQL models", "staging -> intermediate -> mart", "#2563EB")

    st.markdown("#### Pipeline flow")
    st.markdown(
        """
        <div class="riskops-soft-box">
        API health check -> customer CSV import -> dbt models -> dbt tests -> churn model training -> weekly risk report -> pipeline summary.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if weekly.ok and weekly.data:
        st.markdown("#### Latest business output")
        report = weekly.data
        report_cols = st.columns(3)
        report_cols[0].metric("Total customers", report.get("total_customers"))
        report_cols[1].metric("High risk", report.get("high_risk_customers"))
        report_cols[2].metric("Medium risk", report.get("medium_risk_customers"))
        st.write(report.get("executive_summary"))
    else:
        render_warning(f"Weekly report unavailable: {weekly.error}")

    with st.expander("Technical details"):
        safe_json_preview({"ready": ready.data if ready.ok else ready.error, "weekly_report": weekly.data if weekly.ok else weekly.error})


def render_monitoring() -> None:
    section_header(
        "Monitoring",
        "Check health, readiness, ML report status and recent LLM/RAG traces.",
    )

    health = get_health()
    ready = get_ready()
    llm_summary = get_llm_summary()
    ml_report = get_ml_report_status()

    cols = st.columns(4)
    with cols[0]:
        metric_card("Health", "Healthy" if health.ok else "Error", health.error or "API and database", risk_color("low" if health.ok else "high"))
    with cols[1]:
        metric_card("Readiness", "Ready" if ready.ok else "Not ready", ready.error or "Tables, model and folders", risk_color("low" if ready.ok else "high"))
    with cols[2]:
        total_traces = llm_summary.data.get("total_traces") if llm_summary.ok and llm_summary.data else "-"
        metric_card("LLM traces", total_traces, "RAG and agent calls", "#2563EB")
    with cols[3]:
        report_exists = ml_report.data.get("report_exists") if ml_report.ok and isinstance(ml_report.data, dict) else False
        metric_card("ML report", "Available" if report_exists else "Missing", "Data quality HTML", risk_color("low" if report_exists else "medium"))

    if st.button("Generate ML monitoring report", type="primary"):
        result = safe_post("/monitoring/ml/generate-report", timeout=120)
        if result.ok:
            render_success(result.data.get("summary", "ML monitoring report generated."))
        else:
            render_error(f"ML report generation failed: {result.error}")

    if ml_report.ok and isinstance(ml_report.data, dict) and ml_report.data.get("report_exists"):
        st.link_button("Open HTML report", "http://localhost:8000/monitoring/ml/report?format=html")

    traces = get_llm_traces(limit=10)
    if traces.ok and traces.data:
        st.markdown("#### Recent LLM/RAG calls")
        trace_rows = [
            {
                "Timestamp": trace.get("timestamp"),
                "Operation": trace.get("operation"),
                "Tool": trace.get("selected_tool"),
                "Status": trace.get("status"),
                "Latency ms": trace.get("latency_ms"),
                "Sources": trace.get("number_of_sources"),
            }
            for trace in reversed(traces.data)
        ]
        st.dataframe(pd.DataFrame(trace_rows), use_container_width=True, hide_index=True)
    elif traces.ok:
        render_empty_state("No LLM trace recorded yet.")
    else:
        render_warning(f"LLM traces unavailable: {traces.error}")

    with st.expander("Technical details"):
        safe_json_preview(
            {
                "health": health.data if health.ok else health.error,
                "ready": ready.data if ready.ok else ready.error,
                "llm_summary": llm_summary.data if llm_summary.ok else llm_summary.error,
                "ml_report": ml_report.data if ml_report.ok else ml_report.error,
            }
        )


def render_about_project() -> None:
    section_header(
        "About Project",
        "A portfolio V1 showing how AI, data and monitoring support customer risk operations.",
    )

    cols = st.columns(3)
    with cols[0]:
        metric_card("Backend", "FastAPI", "Product APIs and orchestration", "#2563EB")
    with cols[1]:
        metric_card("Data", "PostgreSQL + pgvector", "Business and vector storage", "#2563EB")
    with cols[2]:
        metric_card("AI", "RAG + ML + Agent", "Documents, prediction and routing", "#2563EB")

    st.markdown("#### What the demo shows")
    st.markdown(
        format_list_items(
            [
                "Managers can identify risky customers quickly.",
                "Risk analysis combines ML signals and business rules.",
                "Documents can be searched with RAG and sources.",
                "The agent routes questions to controlled tools.",
                "Monitoring tracks health, ML report status and LLM traces.",
            ]
        ),
        unsafe_allow_html=True,
    )

    st.markdown("#### Recommended demo order")
    st.markdown(
        format_list_items(
            [
                "Open Executive Overview.",
                "Import sample customers in Client Risk.",
                "Analyze one customer and review recommended actions.",
                "Ask the AI Assistant for priority customers.",
                "Upload and process the small RAG demo CSV.",
                "Open Monitoring and generate the ML report.",
            ]
        ),
        unsafe_allow_html=True,
    )


def main() -> None:
    active_page = render_sidebar()
    render_product_header()

    if active_page == "Executive Overview":
        render_executive_overview()
    elif active_page == "Client Risk":
        render_client_risk()
    elif active_page == "Documents and RAG":
        render_documents_rag()
    elif active_page == "AI Assistant":
        render_ai_assistant()
    elif active_page == "Data Pipeline":
        render_data_pipeline()
    elif active_page == "Monitoring":
        render_monitoring()
    elif active_page == "About Project":
        render_about_project()


if __name__ == "__main__":
    main()
