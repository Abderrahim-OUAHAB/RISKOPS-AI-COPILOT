import os
from dataclasses import dataclass
from typing import Any

import requests


API_BASE_URL = os.getenv("API_BASE_URL", os.getenv("API_URL", "http://backend:8000"))
DEFAULT_TIMEOUT = 15


@dataclass
class ApiResult:
    ok: bool
    data: Any = None
    error: str | None = None
    status_code: int | None = None


def _friendly_error(exc: requests.RequestException) -> ApiResult:
    response = getattr(exc, "response", None)
    if response is None:
        if isinstance(exc, requests.Timeout):
            return ApiResult(False, error="The backend request timed out.")
        return ApiResult(False, error="The backend is not available.")

    status_code = response.status_code
    detail = None
    try:
        payload = response.json()
        detail = payload.get("detail") if isinstance(payload, dict) else None
    except ValueError:
        detail = response.text.strip() or None

    messages = {
        400: "The request is invalid.",
        404: "The requested resource was not found.",
        500: "The backend returned an internal error.",
        503: "The service is not ready yet.",
    }
    message = detail or messages.get(status_code, f"Request failed with status {status_code}.")
    return ApiResult(False, error=message, status_code=status_code)


def _parse_response(response: requests.Response) -> ApiResult:
    response.raise_for_status()
    if not response.content:
        return ApiResult(True, data=None, status_code=response.status_code)
    try:
        data = response.json()
    except ValueError:
        data = response.text
    return ApiResult(True, data=data, status_code=response.status_code)


def safe_get(endpoint: str, params: dict[str, Any] | None = None, timeout: int = DEFAULT_TIMEOUT) -> ApiResult:
    try:
        response = requests.get(
            f"{API_BASE_URL}{endpoint}",
            params=params,
            timeout=timeout,
        )
        return _parse_response(response)
    except requests.RequestException as exc:
        return _friendly_error(exc)


def safe_post(
    endpoint: str,
    json: dict[str, Any] | None = None,
    files: dict[str, Any] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> ApiResult:
    try:
        response = requests.post(
            f"{API_BASE_URL}{endpoint}",
            json=json,
            files=files,
            timeout=timeout,
        )
        return _parse_response(response)
    except requests.RequestException as exc:
        return _friendly_error(exc)


def get_health() -> ApiResult:
    return safe_get("/health", timeout=5)


def get_ready() -> ApiResult:
    return safe_get("/ready", timeout=10)


def get_customers() -> ApiResult:
    return safe_get("/customers", timeout=10)


def get_priority_customers() -> ApiResult:
    return safe_get("/risk/priority-customers", timeout=60)


def get_weekly_report() -> ApiResult:
    return safe_get("/reports/weekly-risk", timeout=60)


def get_llm_summary() -> ApiResult:
    return safe_get("/monitoring/llm/summary", timeout=10)


def get_documents() -> ApiResult:
    return safe_get("/documents", timeout=10)


def ask_rag(question: str, document_id: int | None = None, language: str = "en") -> ApiResult:
    return safe_post(
        "/rag/ask",
        json={
            "question": question,
            "document_id": document_id,
            "language": language,
        },
        timeout=120,
    )


def analyze_agent(question: str, language: str = "en") -> ApiResult:
    return safe_post(
        "/agent/analyze",
        json={
            "question": question,
            "language": language,
        },
        timeout=60,
    )


def get_risk_history(customer_id: str, limit: int = 5) -> ApiResult:
    return safe_get("/risk/history", params={"customer_id": customer_id, "limit": limit}, timeout=10)


def get_ml_report_status() -> ApiResult:
    return safe_get("/monitoring/ml/report", timeout=10)


def get_llm_traces(limit: int = 10) -> ApiResult:
    return safe_get("/monitoring/llm/traces", params={"limit": limit}, timeout=10)
