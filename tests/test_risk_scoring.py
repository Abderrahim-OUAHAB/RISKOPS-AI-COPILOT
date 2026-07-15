from pathlib import Path

import pytest

from app.models import Customer
from app.services import model_service
from app.services.model_service import ModelNotTrainedError
from app.services.risk_scoring_service import RISK_WEIGHTS, calculate_global_risk_score


def sample_customer() -> Customer:
    return Customer(
        customer_external_id="sample-account",
        tenure=8,
        monthly_charges=120,
        total_charges=960,
        contract_type="month_to_month",
        support_tickets=7,
        late_payments=3,
        support_ticket_count=7,
        unpaid_invoice_count=3,
    )


def test_risk_score_is_stable_bounded_and_explained():
    customer = sample_customer()
    first = calculate_global_risk_score(customer, 0.82, document_risk_score=60)
    second = calculate_global_risk_score(customer, 0.82, document_risk_score=60)

    assert first == second
    score, reasons, breakdown, weighted_breakdown = first
    assert 0 <= score <= 100
    assert reasons
    assert set(breakdown) == set(RISK_WEIGHTS)
    assert set(weighted_breakdown) == set(RISK_WEIGHTS)


def test_missing_model_artifact_has_controlled_failure(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(model_service.settings, "churn_model_path", str(tmp_path / "missing.pkl"))
    monkeypatch.setattr(model_service.settings, "churn_features_path", str(tmp_path / "missing.json"))

    with pytest.raises(ModelNotTrainedError, match="not trained"):
        model_service.predict_churn_probability(sample_customer())
