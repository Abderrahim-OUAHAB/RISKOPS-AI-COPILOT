from pathlib import Path

import app.api.health as health_api


class ScalarResult:
    def scalar(self):
        return True


class HealthySession:
    bind = object()

    def execute(self, _statement):
        return ScalarResult()


class FailingSession:
    bind = object()

    def execute(self, _statement):
        raise RuntimeError("database unavailable")


class Inspector:
    def get_table_names(self):
        return ["customers", "documents", "document_chunks", "risk_predictions"]


def test_health_returns_expected_structure(client_factory):
    with client_factory(HealthySession()) as client:
        response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database"]["status"] == "ok"
    assert payload["vector_extension"]["status"] == "available"


def test_ready_reports_dependencies_ready(client_factory, monkeypatch, tmp_path: Path):
    model_path = tmp_path / "model.pkl"
    model_path.write_bytes(b"model")
    monkeypatch.setattr(health_api.settings, "churn_model_path", str(model_path))
    monkeypatch.setattr(
        health_api.settings,
        "ml_monitoring_report_path",
        str(tmp_path / "monitoring" / "report.html"),
    )
    monkeypatch.setattr(
        health_api.settings,
        "llm_traces_path",
        str(tmp_path / "monitoring" / "traces.jsonl"),
    )
    monkeypatch.setattr(health_api, "inspect", lambda _bind: Inspector())

    with client_factory(HealthySession()) as client:
        response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["ready"] is True


def test_ready_returns_503_on_database_failure(client_factory, monkeypatch, tmp_path: Path):
    monkeypatch.setattr(health_api.settings, "churn_model_path", str(tmp_path / "missing.pkl"))
    monkeypatch.setattr(
        health_api.settings,
        "ml_monitoring_report_path",
        str(tmp_path / "monitoring" / "report.html"),
    )
    monkeypatch.setattr(
        health_api.settings,
        "llm_traces_path",
        str(tmp_path / "monitoring" / "traces.jsonl"),
    )

    with client_factory(FailingSession()) as client:
        response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["ready"] is False
    assert response.json()["checks"]["database"] is False
