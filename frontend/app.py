import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://backend:8000")

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
            st.error(f"Upload failed for {uploaded_file.name}: {exc}")

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
                    "created_at": document["created_at"],
                }
                for document in documents
            ],
            use_container_width=True,
        )
except requests.RequestException:
    st.warning("Document list unavailable until the API is reachable.")

st.subheader("Ask a question")
st.text_input("Example: Which customers are at risk this week?")
st.button("Ask Copilot", disabled=True)
