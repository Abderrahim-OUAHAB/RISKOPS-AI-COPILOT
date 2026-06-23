import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://backend:8000")


def get_api_error(exc: requests.RequestException) -> str:
    response = getattr(exc, "response", None)
    if response is None:
        return str(exc)

    try:
        detail = response.json().get("detail")
    except ValueError:
        detail = response.text

    return detail or str(exc)

st.set_page_config(
    page_title="AI RiskOps Copilot",
    page_icon="",
    layout="wide",
)

st.title("AI RiskOps Copilot")
st.caption("MVP portfolio for AI Engineering, Data Engineering, MLOps and LLMOps.")

with st.sidebar:
    st.header("Project modules")
    st.write("1. Upload documents")
    st.write("2. RAG with sources")
    st.write("3. Churn prediction")
    st.write("4. Risk Score")
    st.write("5. AI agent")
    st.write("6. Data pipeline")

col1, col2 = st.columns(2)

with col1:
    st.subheader("System status")
    if st.button("Check API health"):
        try:
            response = requests.get(f"{API_URL}/health", timeout=5)
            st.success(response.json())
        except requests.RequestException as exc:
            st.error(f"API is not reachable: {exc}")

with col2:
    st.subheader("Risk Score preview")
    st.metric("Global risk score", "Not calculated yet")
    st.info("The first version will calculate churn risk from customer data.")

st.divider()

st.subheader("Upload area")
uploaded_files = st.file_uploader(
    "Upload PDF or CSV files",
    type=["pdf", "csv"],
    accept_multiple_files=True,
)

if uploaded_files and st.button("Upload selected files"):
    for uploaded_file in uploaded_files:
        try:
            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type or "application/octet-stream",
                )
            }
            response = requests.post(
                f"{API_URL}/documents/upload",
                files=files,
                timeout=30,
            )
            response.raise_for_status()
            document = response.json()
            st.success(
                f"{document['filename']} uploaded with document id {document['id']}."
            )
        except requests.RequestException as exc:
            st.error(f"Upload failed for {uploaded_file.name}: {get_api_error(exc)}")

documents = []
try:
    documents_response = requests.get(f"{API_URL}/documents", timeout=5)
    documents_response.raise_for_status()
    documents = documents_response.json()
    if documents:
        st.dataframe(
            [
                {
                    "id": document["id"],
                    "filename": document["filename"],
                    "type": document["document_type"],
                    "status": document["status"],
                    "created_at": document["created_at"],
                    "processed_at": document["processed_at"],
                }
                for document in documents
            ],
            use_container_width=True,
        )
except requests.RequestException:
    st.warning("Document list unavailable until the API is reachable.")

if documents:
    st.subheader("Document processing")
    document_options = {
        f"{document['id']} - {document['filename']} ({document['status']})": document[
            "id"
        ]
        for document in documents
    }
    selected_document_label = st.selectbox(
        "Document",
        options=list(document_options.keys()),
    )
    selected_document_id = document_options[selected_document_label]

    if st.button("Process selected document"):
        try:
            response = requests.post(
                f"{API_URL}/documents/{selected_document_id}/process",
                timeout=120,
            )
            response.raise_for_status()
            result = response.json()
            st.success(
                f"Document {result['document_id']} processed: "
                f"{result['chunks_created']} chunks created."
            )
        except requests.RequestException as exc:
            st.error(f"Processing failed: {get_api_error(exc)}")

    st.subheader("Ask a question")
    with st.form("rag-question-form"):
        question = st.text_input(
            "Question",
            value="Resume les risques principaux",
        )
        ask_submitted = st.form_submit_button("Ask Copilot")

    if ask_submitted:
        try:
            response = requests.post(
                f"{API_URL}/rag/ask",
                json={
                    "question": question,
                    "document_id": selected_document_id,
                },
                timeout=120,
            )
            response.raise_for_status()
            result = response.json()
            st.write(result["answer"])

            if result["sources"]:
                st.caption("Sources")
                for source in result["sources"]:
                    with st.expander(
                        f"Document {source['document_id']} - "
                        f"chunk {source['chunk_id']} - "
                        f"score {source['similarity_score']}"
                    ):
                        st.write(source["content_preview"])
        except requests.RequestException as exc:
            st.error(f"RAG request failed: {get_api_error(exc)}")
else:
    st.subheader("Ask a question")
    st.text_input("Example: Which customers are at risk this week?", disabled=True)
    st.button("Ask Copilot", disabled=True)

st.divider()

st.subheader("Machine Learning")
customer_file = st.file_uploader(
    "Import customer CSV",
    type=["csv"],
    accept_multiple_files=False,
    key="customer_csv_import",
)

if customer_file and st.button("Import customers"):
    try:
        files = {
            "file": (
                customer_file.name,
                customer_file.getvalue(),
                customer_file.type or "text/csv",
            )
        }
        response = requests.post(
            f"{API_URL}/customers/import",
            files=files,
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()
        st.success(f"{result['imported_count']} customers imported.")
    except requests.RequestException as exc:
        st.error(f"Customer import failed: {get_api_error(exc)}")

customers = []
try:
    customers_response = requests.get(f"{API_URL}/customers", timeout=5)
    customers_response.raise_for_status()
    customers = customers_response.json()
    if customers:
        st.dataframe(
            [
                {
                    "customer_id": customer["customer_external_id"],
                    "name": customer["name"],
                    "tenure": customer["tenure"],
                    "contract_type": customer["contract_type"],
                    "support_tickets": customer["support_tickets"],
                    "late_payments": customer["late_payments"],
                    "risk_score": customer["risk_score"],
                    "risk_level": customer["risk_level"],
                }
                for customer in customers
            ],
            use_container_width=True,
        )
except requests.RequestException:
    st.warning("Customer list unavailable until the API is reachable.")

if customers:
    customer_options = {
        f"{customer['customer_external_id']} - {customer['name']}": customer[
            "customer_external_id"
        ]
        for customer in customers
    }
    selected_customer_label = st.selectbox(
        "Customer for churn prediction",
        options=list(customer_options.keys()),
    )
    selected_customer_id = customer_options[selected_customer_label]

    if st.button("Predict churn risk"):
        try:
            response = requests.post(
                f"{API_URL}/risk/predict",
                json={"customer_id": selected_customer_id},
                timeout=30,
            )
            response.raise_for_status()
            prediction = response.json()
            metric_col1, metric_col2 = st.columns(2)
            metric_col1.metric("Risk score", prediction["risk_score"])
            metric_col2.metric("Risk level", prediction["risk_level"])
            st.write(f"Churn probability: {prediction['churn_probability']}")
            st.write("Reasons")
            for reason in prediction["reasons"]:
                st.write(f"- {reason}")
        except requests.RequestException as exc:
            st.error(f"Prediction failed: {get_api_error(exc)}")

st.divider()

st.subheader("RiskOps")

priority_customers = []
try:
    priority_response = requests.get(f"{API_URL}/risk/priority-customers", timeout=60)
    priority_response.raise_for_status()
    priority_customers = priority_response.json()
    if priority_customers:
        top_customer = priority_customers[0]
        risk_col1, risk_col2, risk_col3 = st.columns(3)
        risk_col1.metric("Top risk score", top_customer["risk_score"])
        risk_col2.metric("Top risk level", top_customer["risk_level"])
        risk_col3.metric("Priority customers", len(priority_customers))
        st.dataframe(
            [
                {
                    "customer_id": customer["customer_id"],
                    "name": customer["name"],
                    "risk_score": customer["risk_score"],
                    "risk_level": customer["risk_level"],
                    "top_reasons": ", ".join(customer["top_reasons"]),
                    "actions": ", ".join(customer["recommended_actions"]),
                }
                for customer in priority_customers[:10]
            ],
            use_container_width=True,
        )
except requests.RequestException as exc:
    st.warning(f"RiskOps priority dashboard unavailable: {get_api_error(exc)}")

if customers:
    riskops_customer_options = {
        f"{customer['customer_external_id']} - {customer['name']}": customer[
            "customer_external_id"
        ]
        for customer in customers
    }
    riskops_customer_label = st.selectbox(
        "Customer for RiskOps analysis",
        options=list(riskops_customer_options.keys()),
        key="riskops_customer",
    )
    riskops_customer_id = riskops_customer_options[riskops_customer_label]

    if st.button("Analyze customer risk"):
        try:
            response = requests.post(
                f"{API_URL}/risk/analyze-customer",
                json={"customer_id": riskops_customer_id},
                timeout=60,
            )
            response.raise_for_status()
            analysis = response.json()
            analysis_col1, analysis_col2 = st.columns(2)
            analysis_col1.metric("Risk score", analysis["risk_score"])
            analysis_col2.metric("Risk level", analysis["risk_level"])
            st.write(f"Churn probability: {analysis['churn_probability']}")
            st.write("Reasons")
            for reason in analysis["reasons"]:
                st.write(f"- {reason}")
            st.write("Recommended actions")
            for action in analysis["recommended_actions"]:
                st.write(f"- {action}")
        except requests.RequestException as exc:
            st.error(f"RiskOps analysis failed: {get_api_error(exc)}")

    try:
        history_response = requests.get(
            f"{API_URL}/risk/history",
            params={"customer_id": riskops_customer_id, "limit": 5},
            timeout=10,
        )
        history_response.raise_for_status()
        history = history_response.json()
        if history:
            st.caption("Recent prediction history")
            st.dataframe(
                [
                    {
                        "created_at": item["created_at"],
                        "risk_score": item["risk_score"],
                        "risk_level": item["risk_level"],
                        "churn_probability": item["churn_probability"],
                    }
                    for item in history
                ],
                use_container_width=True,
            )
    except requests.RequestException as exc:
        st.warning(f"Prediction history unavailable: {get_api_error(exc)}")

try:
    report_response = requests.get(f"{API_URL}/reports/weekly-risk", timeout=60)
    report_response.raise_for_status()
    weekly_report = report_response.json()
    st.subheader("Weekly risk report")
    report_col1, report_col2, report_col3 = st.columns(3)
    report_col1.metric("High risk", weekly_report["high_risk_customers"])
    report_col2.metric("Medium risk", weekly_report["medium_risk_customers"])
    report_col3.metric("Low risk", weekly_report["low_risk_customers"])
    st.write(weekly_report["executive_summary"])
    with st.expander("Recommended actions"):
        for action in weekly_report["recommended_actions"]:
            st.write(f"- {action}")
except requests.RequestException as exc:
    st.warning(f"Weekly risk report unavailable: {get_api_error(exc)}")

with st.form("riskops-agent-form"):
    agent_question = st.text_input(
        "RiskOps agent question",
        value="Quels clients sont a risque cette semaine ?",
    )
    agent_submitted = st.form_submit_button("Ask RiskOps agent")

if agent_submitted:
    try:
        response = requests.post(
            f"{API_URL}/agent/analyze",
            json={"question": agent_question},
            timeout=60,
        )
        response.raise_for_status()
        agent_result = response.json()
        st.write(agent_result["answer"])
        st.caption(f"Selected tool: {agent_result['selected_tool']}")
        if agent_result["data"]:
            st.json(agent_result["data"])
    except requests.RequestException as exc:
        st.error(f"Agent failed: {get_api_error(exc)}")

st.divider()

st.subheader("Data Pipeline")

pipeline_col1, pipeline_col2 = st.columns(2)

with pipeline_col1:
    st.write("Backend status")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        response.raise_for_status()
        st.success(response.json())
    except requests.RequestException as exc:
        st.warning(f"Backend unavailable: {get_api_error(exc)}")

with pipeline_col2:
    st.write("Airflow")
    st.info("Airflow UI: http://localhost:8080")
    st.caption("Local credentials: admin / admin")

st.write("Pipeline flow")
st.write(
    "API health check -> customer CSV import -> dbt models -> dbt tests -> "
    "churn model training -> weekly risk report -> pipeline summary."
)

try:
    pipeline_report_response = requests.get(
        f"{API_URL}/reports/weekly-risk",
        timeout=60,
    )
    pipeline_report_response.raise_for_status()
    pipeline_report = pipeline_report_response.json()
    pipeline_report_col1, pipeline_report_col2, pipeline_report_col3 = st.columns(3)
    pipeline_report_col1.metric("Total customers", pipeline_report["total_customers"])
    pipeline_report_col2.metric("High risk", pipeline_report["high_risk_customers"])
    pipeline_report_col3.metric("Medium risk", pipeline_report["medium_risk_customers"])
    st.write(pipeline_report["executive_summary"])
except requests.RequestException as exc:
    st.warning(f"Latest weekly risk report unavailable: {get_api_error(exc)}")
