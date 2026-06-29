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


def render_executive_overview() -> None:
    section_header(
        "Executive Overview",
        "A manager-friendly view of customer risk, recommended action and platform status.",
    )

    priority = get_priority_customers()
    weekly = get_weekly_report()
    ready = get_ready()
    llm_summary = get_llm_summary()

    priority_rows = priority.data if priority.ok and priority.data else []
    report = weekly.data if weekly.ok and weekly.data else {}

    top_customer = priority_rows[0] if priority_rows else {}
    cols = st.columns(4)
    with cols[0]:
        metric_card("Top risk score", top_customer.get("risk_score", "-"), "Highest current customer score", "#DC2626")
    with cols[1]:
        metric_card("High risk", report.get("high_risk_customers", "-"), "Customers needing fast action", "#DC2626")
    with cols[2]:
        metric_card("Medium risk", report.get("medium_risk_customers", "-"), "Customers to watch", "#F59E0B")
    with cols[3]:
        status = "ready" if ready.ok else "not_ready"
        metric_card("System status", status.replace("_", " ").title(), ready.error or "Backend readiness check", risk_color("low" if ready.ok else "high"))

    if report.get("executive_summary"):
        st.markdown("#### Management summary")
        st.write(report["executive_summary"])
    elif not weekly.ok:
        render_warning(f"Weekly report unavailable: {weekly.error}")

    section_header("Priority customers", "The first customers a manager should review.")
    if priority_rows:
        _risk_table(priority_rows[:5])
    elif not priority.ok:
        render_warning(f"Priority customers unavailable: {priority.error}")
    else:
        render_empty_state("No priority customers available yet.")

    with st.expander("Technical details"):
        safe_json_preview(
            {
                "weekly_report": report,
                "readiness_status": ready.status_code,
                "llm_summary": llm_summary.data if llm_summary.ok else llm_summary.error,
            }
        )


def render_client_risk() -> None:
    section_header(
        "Client Risk",
        "Import customers, review risk signals and generate a customer risk analysis.",
    )

    customer_file = st.file_uploader("Import customer CSV", type=["csv"], accept_multiple_files=False)
    if customer_file and st.button("Import customers", type="primary"):
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

    customers = _customers()
    section_header("Customer portfolio", "Structured customer data from PostgreSQL.")
    _risk_table(customers)

    if not customers:
        return

    options = _customer_options(customers)
    selected_label = st.selectbox("Customer", list(options.keys()))
    selected_customer_id = options[selected_label]

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Predict churn risk", use_container_width=True):
            result = safe_post("/risk/predict", json={"customer_id": selected_customer_id}, timeout=60)
            if result.ok:
                prediction = result.data
                render_risk_score(prediction.get("risk_score"), prediction.get("risk_level"))
                st.markdown(format_list_items(prediction.get("reasons")), unsafe_allow_html=True)
                st.markdown("Recommended actions")
                st.markdown(format_list_items(prediction.get("recommended_actions")), unsafe_allow_html=True)
            else:
                render_error(f"Prediction failed: {result.error}")

    with col2:
        if st.button("Analyze customer risk", use_container_width=True, type="primary"):
            result = safe_post("/risk/analyze-customer", json={"customer_id": selected_customer_id}, timeout=60)
            if result.ok:
                analysis = result.data
                render_risk_score(analysis.get("risk_score"), analysis.get("risk_level"))
                st.markdown("Reasons")
                st.markdown(format_list_items(analysis.get("reasons")), unsafe_allow_html=True)
                st.markdown("Recommended actions")
                st.markdown(format_list_items(analysis.get("recommended_actions")), unsafe_allow_html=True)
            else:
                render_error(f"RiskOps analysis failed: {result.error}")

    history = get_risk_history(selected_customer_id)
    if history.ok and history.data:
        with st.expander("Recent prediction history"):
            st.dataframe(pd.DataFrame(history.data), use_container_width=True, hide_index=True)


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
        "AI Assistant",
        "Ask business questions. The controlled agent routes them to risk, report or document tools.",
    )

    examples = [
        "Which customers are at risk this week?",
        "Analyze CUST-001",
        "Generate a weekly risk summary",
        "What does the uploaded document say about high risk customers?",
    ]
    selected_example = st.selectbox("Example question", examples)

    with st.form("riskops-agent-form"):
        question = st.text_input("Question", value=selected_example)
        submitted = st.form_submit_button("Ask RiskOps agent", type="primary")

    if submitted:
        result = safe_post("/agent/analyze", json={"question": question}, timeout=60)
        if result.ok:
            st.markdown("#### Answer")
            st.write(result.data.get("answer"))
            st.markdown(status_badge(result.data.get("selected_tool")), unsafe_allow_html=True)
            with st.expander("Technical details"):
                safe_json_preview(result.data)
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
