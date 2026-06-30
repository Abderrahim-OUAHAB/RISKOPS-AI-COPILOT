from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models import Customer, RiskPrediction
from app.services.document_intelligence_service import (
    DocumentRiskResult,
    calculate_document_risk,
)
from app.services.model_service import predict_churn_probability
from app.services.recommendation_service import recommend_actions

MODEL_VERSION = "xgboost-riskops-v2"

RISK_WEIGHTS = {
    "ml": 0.35,
    "payment": 0.20,
    "support": 0.15,
    "contract": 0.10,
    "document": 0.10,
    "trend": 0.05,
    "recency": 0.05,
}


@dataclass
class RiskAnalysisResult:
    customer_id: str
    risk_score: int
    risk_level: str
    churn_probability: float
    reasons: list[str]
    recommended_actions: list[str]
    prediction_id: int
    confidence: float
    score_breakdown: dict[str, float]
    weighted_score_breakdown: dict[str, float]
    business_impact: str
    next_best_action: str
    owner: str
    due_date: str
    language: str
    document_risk_score: int
    document_risk_level: str
    document_risk_signals: list[str]
    document_evidence: list[dict[str, Any]]


def analyze_customer_risk(
    db: Session,
    customer: Customer,
    language: str = "en",
) -> RiskAnalysisResult:
    language = _normalize_language(language)
    churn_probability = predict_churn_probability(customer)
    document_risk = calculate_document_risk(
        db=db,
        customer_id=customer.customer_external_id or "",
        language=language,
    )
    risk_score, reasons, score_breakdown, weighted_score_breakdown = (
        calculate_global_risk_score(
            customer,
            churn_probability,
            language=language,
            document_risk_score=document_risk.document_risk_score,
        )
    )
    risk_level = risk_level_from_score(risk_score)
    english_reasons = _english_reasons(customer, churn_probability, document_risk)
    recommended_actions = recommend_actions(customer, english_reasons, risk_score)
    if document_risk.document_risk_score >= 70:
        recommended_actions.append("Review document evidence")
    elif document_risk.document_risk_score >= 40:
        recommended_actions.append("Validate document risk signals")
    if language == "fr":
        recommended_actions = [_translate_action(action) for action in recommended_actions]
    recommended_actions = list(dict.fromkeys(recommended_actions))
    confidence = _confidence_score(customer, document_risk)
    business_impact = _business_impact(customer, risk_level, language, document_risk)
    next_best_action = _next_best_action(weighted_score_breakdown, risk_level, language)
    owner = _recommended_owner(weighted_score_breakdown, language)
    due_date = _recommended_due_date(risk_level)

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
        confidence=confidence,
        score_breakdown=score_breakdown,
        weighted_score_breakdown=weighted_score_breakdown,
        business_impact=business_impact,
        next_best_action=next_best_action,
        owner=owner,
        due_date=due_date,
        language=language,
        document_risk_score=document_risk.document_risk_score,
        document_risk_level=document_risk.document_risk_level,
        document_risk_signals=document_risk.document_risk_signals,
        document_evidence=document_risk.document_evidence,
    )


def calculate_global_risk_score(
    customer: Customer,
    churn_probability: float,
    language: str = "en",
    document_risk_score: int = 0,
) -> tuple[int, list[str], dict[str, float], dict[str, float]]:
    return _calculate_global_risk_score(
        customer,
        churn_probability,
        language=_normalize_language(language),
        document_risk_score=document_risk_score,
    )


def _calculate_global_risk_score(
    customer: Customer,
    churn_probability: float,
    language: str,
    document_risk_score: int,
) -> tuple[int, list[str], dict[str, float], dict[str, float]]:
    score_breakdown = _score_breakdown(
        customer,
        churn_probability,
        document_risk_score=document_risk_score,
    )
    weighted_score_breakdown = {
        key: round(score_breakdown[key] * weight, 2)
        for key, weight in RISK_WEIGHTS.items()
    }
    risk_score = int(round(max(0, min(100, sum(weighted_score_breakdown.values())))))
    english_reasons = _english_reasons(customer, churn_probability)
    if document_risk_score >= 70:
        english_reasons.append("High document risk evidence")
    elif document_risk_score >= 40:
        english_reasons.append("Document risk signals detected")
    reasons = _localized_reasons(english_reasons, language)
    if not reasons:
        reasons.append(
            "No major risk driver detected"
            if language == "en"
            else "Aucun facteur de risque majeur detecte"
        )

    return risk_score, reasons, score_breakdown, weighted_score_breakdown


def risk_level_from_score(risk_score: int) -> str:
    if risk_score >= 70:
        return "high"
    if risk_score >= 40:
        return "medium"
    return "low"


def _normalize_contract_type(value: object) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "monthly": "month_to_month",
        "month": "month_to_month",
        "month_to_month": "month_to_month",
        "one_year": "one_year",
        "1_year": "one_year",
        "annual": "one_year",
        "two_year": "two_year",
        "2_year": "two_year",
        "biannual": "two_year",
    }
    return aliases.get(normalized, normalized)


def _normalize_language(language: str | None) -> str:
    return "fr" if str(language or "en").strip().lower().startswith("fr") else "en"


def _score_breakdown(
    customer: Customer,
    churn_probability: float,
    document_risk_score: int = 0,
) -> dict[str, float]:
    late_payments = max(customer.late_payments or 0, customer.unpaid_invoice_count or 0)
    support_tickets = max(customer.support_tickets or 0, customer.support_ticket_count or 0)
    contract_type = _normalize_contract_type(customer.contract_type)
    tenure = customer.tenure

    contract_risk = {
        "month_to_month": 100.0,
        "one_year": 40.0,
        "two_year": 10.0,
    }.get(contract_type, 0.0)

    payment_risk = min(max(late_payments, 0), 4) / 4 * 100
    support_risk = min(max(support_tickets, 0), 10) / 10 * 100
    trend_risk = min((payment_risk + support_risk) / 2, 100)

    document_risk = max(0, min(100, document_risk_score))
    # No event timestamp exists for recent risk signals yet; short tenure is the closest stable proxy.
    recency_risk = 0.0
    if tenure is not None:
        if tenure < 6:
            recency_risk = 100.0
        elif tenure < 12:
            recency_risk = 60.0

    return {
        "ml": round(min(max(churn_probability, 0.0), 1.0) * 100, 2),
        "payment": round(payment_risk, 2),
        "support": round(support_risk, 2),
        "contract": round(contract_risk, 2),
        "document": round(document_risk, 2),
        "trend": round(trend_risk, 2),
        "recency": round(recency_risk, 2),
    }


def _english_reasons(
    customer: Customer,
    churn_probability: float,
    document_risk: DocumentRiskResult | None = None,
) -> list[str]:
    reasons: list[str] = []
    if churn_probability >= 0.7:
        reasons.append("High churn probability")
    elif churn_probability >= 0.4:
        reasons.append("Moderate churn probability")
    if max(customer.late_payments or 0, customer.unpaid_invoice_count or 0) > 0:
        reasons.append("Late payments detected")
    if max(customer.support_tickets or 0, customer.support_ticket_count or 0) >= 5:
        reasons.append("Many support tickets")
    if customer.tenure is not None and customer.tenure < 6:
        reasons.append("Very short customer tenure")
    elif customer.tenure is not None and customer.tenure < 12:
        reasons.append("Short customer tenure")
    if _normalize_contract_type(customer.contract_type) == "month_to_month":
        reasons.append("Month-to-month contract")
    total_charges = float(customer.total_charges or 0)
    if total_charges >= 5000 and churn_probability >= 0.4:
        reasons.append("High value exposure")
    if document_risk is not None and document_risk.document_risk_score >= 70:
        reasons.append("High document risk evidence")
    elif document_risk is not None and document_risk.document_risk_score >= 40:
        reasons.append("Document risk signals detected")
    return reasons


def _localized_reasons(reasons: list[str], language: str) -> list[str]:
    if language == "en":
        return reasons
    translations = {
        "High churn probability": "Probabilite de churn elevee",
        "Moderate churn probability": "Probabilite de churn moderee",
        "Late payments detected": "Retards de paiement detectes",
        "Many support tickets": "Nombreux tickets support",
        "Very short customer tenure": "Anciennete client tres courte",
        "Short customer tenure": "Anciennete client courte",
        "Month-to-month contract": "Contrat mensuel",
        "High value exposure": "Exposition revenu elevee",
        "High document risk evidence": "Preuves documentaires de risque eleve",
        "Document risk signals detected": "Signaux de risque documentaire detectes",
    }
    return [translations.get(reason, reason) for reason in reasons]


def _translate_action(action: str) -> str:
    translations = {
        "Contact customer within 48 hours": "Contacter le client sous 48 heures",
        "Offer a retention discussion": "Proposer une discussion de retention",
        "Schedule a follow-up meeting": "Planifier un rendez-vous de suivi",
        "Monitor customer for 7 days": "Surveiller le compte pendant 7 jours",
        "Review unpaid invoices": "Verifier les factures impayees",
        "Escalate recent support issues": "Escalader les problemes support recents",
        "Propose an onboarding check-in": "Proposer un point d'onboarding",
        "Offer a longer-term contract incentive": "Proposer une incitation a contrat plus long",
        "Assign account owner review": "Assigner une revue par le responsable de compte",
        "Review document evidence": "Revoir les preuves documentaires",
        "Validate document risk signals": "Valider les signaux de risque documentaire",
    }
    return translations.get(action, action)


def _confidence_score(
    customer: Customer,
    document_risk: DocumentRiskResult | None = None,
) -> float:
    fields = [
        customer.tenure,
        customer.monthly_charges,
        customer.total_charges,
        customer.contract_type,
        customer.support_tickets,
        customer.late_payments,
    ]
    completeness = sum(value is not None for value in fields) / len(fields)
    if completeness >= 0.95:
        base_confidence = 0.9
    elif completeness >= 0.65:
        base_confidence = 0.7
    elif completeness >= 0.35:
        base_confidence = 0.55
    else:
        base_confidence = 0.3

    if document_risk is not None and document_risk.linked_documents:
        base_confidence = min(0.95, base_confidence + 0.03)
    return round(base_confidence, 2)


def _business_impact(
    customer: Customer,
    risk_level: str,
    language: str,
    document_risk: DocumentRiskResult | None = None,
) -> str:
    payment_signal = max(customer.late_payments or 0, customer.unpaid_invoice_count or 0) > 0
    support_signal = max(customer.support_tickets or 0, customer.support_ticket_count or 0) >= 5
    short_tenure = customer.tenure is not None and customer.tenure < 12

    if language == "fr":
        if document_risk is not None and document_risk.document_risk_score >= 70:
            return "Risque documentaire eleve avec preuves liees aux paiements, au contrat ou au support."
        if risk_level == "high":
            return "Exposition revenu elevee avec retards de paiement et signaux support repetes."
        if risk_level == "medium" and (support_signal or short_tenure):
            return "Risque de churn moyen lie a l'activite support et a l'anciennete limitee."
        if payment_signal:
            return "Risque operationnel lie au comportement de paiement a surveiller."
        return "Risque actuel faible avec usage et comportement de paiement stables."

    if document_risk is not None and document_risk.document_risk_score >= 70:
        return "High document-backed risk with evidence linked to payments, contract or support."
    if risk_level == "high":
        return "High revenue exposure with payment delays and repeated support signals."
    if risk_level == "medium" and (support_signal or short_tenure):
        return "Medium churn exposure driven by support activity and short tenure."
    if payment_signal:
        return "Operational exposure from payment behavior that should be monitored."
    return "Low current risk with stable usage and payment behavior."


def _next_best_action(
    weighted_score_breakdown: dict[str, float],
    risk_level: str,
    language: str,
) -> str:
    dominant_signal = max(weighted_score_breakdown, key=weighted_score_breakdown.get)
    if language == "fr":
        if risk_level == "high":
            return "Contacter le client sous 48 heures"
        if dominant_signal == "payment":
            return "Verifier les factures impayees"
        if dominant_signal == "support":
            return "Escalader le probleme support"
        if dominant_signal in {"contract", "ml"}:
            return "Preparer une offre de retention"
        return "Surveiller le compte la semaine prochaine"

    if risk_level == "high":
        return "Contact customer within 48 hours"
    if dominant_signal == "payment":
        return "Review unpaid invoices"
    if dominant_signal == "support":
        return "Escalate support issue"
    if dominant_signal in {"contract", "ml"}:
        return "Prepare retention offer"
    return "Monitor account next week"


def _recommended_owner(weighted_score_breakdown: dict[str, float], language: str) -> str:
    dominant_signal = max(weighted_score_breakdown, key=weighted_score_breakdown.get)
    if dominant_signal == "payment":
        return "Equipe finance" if language == "fr" else "Finance Team"
    if dominant_signal == "support":
        return "Responsable support" if language == "fr" else "Support Lead"
    if dominant_signal in {"ml", "contract", "trend"}:
        return "Responsable de compte" if language == "fr" else "Account Manager"
    return "Customer Success Manager"


def _recommended_due_date(risk_level: str) -> str:
    days = {"high": 2, "medium": 7, "low": 14}.get(risk_level, 7)
    return (date.today() + timedelta(days=days)).isoformat()
