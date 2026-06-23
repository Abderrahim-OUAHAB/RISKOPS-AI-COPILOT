from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import Customer, RiskPrediction
from app.services.model_service import predict_churn_probability
from app.services.recommendation_service import recommend_actions

MODEL_VERSION = "xgboost-riskops-v1"


@dataclass
class RiskAnalysisResult:
    customer_id: str
    risk_score: int
    risk_level: str
    churn_probability: float
    reasons: list[str]
    recommended_actions: list[str]
    prediction_id: int


def analyze_customer_risk(db: Session, customer: Customer) -> RiskAnalysisResult:
    churn_probability = predict_churn_probability(customer)
    risk_score, reasons = calculate_global_risk_score(customer, churn_probability)
    risk_level = risk_level_from_score(risk_score)
    recommended_actions = recommend_actions(customer, reasons, risk_score)

    customer.churn_probability = Decimal(str(churn_probability))
    customer.risk_score = Decimal(risk_score)
    customer.risk_level = risk_level

    prediction = RiskPrediction(
        customer_id=customer.customer_external_id or "",
        churn_probability=Decimal(str(churn_probability)),
        risk_score=risk_score,
        risk_level=risk_level,
        reasons=reasons,
        recommended_actions=recommended_actions,
        model_version=MODEL_VERSION,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    db.refresh(customer)

    return RiskAnalysisResult(
        customer_id=customer.customer_external_id or "",
        risk_score=risk_score,
        risk_level=risk_level,
        churn_probability=round(churn_probability, 4),
        reasons=reasons,
        recommended_actions=recommended_actions,
        prediction_id=prediction.id,
    )


def calculate_global_risk_score(
    customer: Customer,
    churn_probability: float,
) -> tuple[int, list[str]]:
    reasons: list[str] = []
    score = 0.0

    score += min(max(churn_probability, 0.0), 1.0) * 50
    if churn_probability >= 0.7:
        reasons.append("High churn probability")
    elif churn_probability >= 0.4:
        reasons.append("Moderate churn probability")

    late_payments = customer.late_payments or 0
    score += min(late_payments, 4) / 4 * 20
    if late_payments > 0:
        reasons.append("Late payments detected")

    support_tickets = customer.support_tickets or 0
    score += min(support_tickets, 10) / 10 * 15
    if support_tickets >= 5:
        reasons.append("Many support tickets")

    tenure = customer.tenure or 0
    if tenure < 6:
        score += 8
        reasons.append("Very short customer tenure")
    elif tenure < 12:
        score += 5
        reasons.append("Short customer tenure")

    if _normalize_contract_type(customer.contract_type) == "month_to_month":
        score += 5
        reasons.append("Month-to-month contract")

    total_charges = float(customer.total_charges or 0)
    if total_charges >= 5000 and churn_probability >= 0.4:
        score += 2
        reasons.append("High value exposure")

    risk_score = int(round(max(0, min(100, score))))
    if not reasons:
        reasons.append("No major risk driver detected")

    return risk_score, reasons


def risk_level_from_score(risk_score: int) -> str:
    if risk_score >= 70:
        return "high"
    if risk_score >= 40:
        return "medium"
    return "low"


def _normalize_contract_type(value: object) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
