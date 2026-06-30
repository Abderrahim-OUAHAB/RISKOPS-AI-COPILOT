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


def analyze_customer_risk(customer_id: str, language: str = "en") -> ApiResult:
    return safe_post(
        "/risk/analyze-customer",
        json={"customer_id": customer_id, "language": language},
        timeout=60,
    )


def explain_customer_risk(customer_id: str, language: str = "en") -> ApiResult:
    return safe_get(
        f"/risk/explain/{customer_id}",
        params={"language": language},
        timeout=60,
    )


def get_document_risk(customer_id: str, language: str = "en") -> ApiResult:
    return safe_get(
        f"/risk/document-risk/{customer_id}",
        params={"language": language},
        timeout=60,
    )


def get_client_360(customer_id: str, language: str = "en") -> ApiResult:
    return safe_get(
        f"/risk/client-360/{customer_id}",
        params={"language": language},
        timeout=60,
    )


def get_action_plan(limit: int = 5, language: str = "en") -> ApiResult:
    return safe_get(
        "/actions/plan",
        params={"limit": limit, "language": language},
        timeout=60,
    )


def sync_recommended_actions(limit: int = 10, language: str = "en") -> ApiResult:
    return safe_post(
        f"/actions/sync?limit={limit}&language={language}",
        json=None,
        timeout=60,
    )


def get_actions(
    status: str | None = None,
    owner: str | None = None,
    priority: str | None = None,
    customer_id: str | None = None,
    limit: int = 100,
) -> ApiResult:
    params = {
        "status": status,
        "owner": owner,
        "priority": priority,
        "customer_id": customer_id,
        "limit": limit,
    }
    return safe_get(
        "/actions",
        params={key: value for key, value in params.items() if value},
        timeout=30,
    )


def get_action_board(language: str = "en", limit: int = 100) -> ApiResult:
    return safe_get(
        "/actions/board",
        params={"language": language, "limit": limit},
        timeout=30,
    )


def update_action(action_id: str, payload: dict[str, Any]) -> ApiResult:
    try:
        response = requests.patch(
            f"{API_BASE_URL}/actions/{action_id}",
            json=payload,
            timeout=30,
        )
        return _parse_response(response)
    except requests.RequestException as exc:
        return _friendly_error(exc)


def complete_action(action_id: str) -> ApiResult:
    return safe_post(f"/actions/{action_id}/complete", timeout=30)


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
