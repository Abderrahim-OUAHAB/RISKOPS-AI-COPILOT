from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Customer
from app.schemas import PriorityCustomerRead, WeeklyRiskReport
from app.services.risk_scoring_service import analyze_customer_risk


def get_priority_customers(
    db: Session,
    limit: int | None = None,
) -> list[PriorityCustomerRead]:
    customers = list(db.scalars(select(Customer).order_by(Customer.customer_external_id)))
    priority_rows: list[PriorityCustomerRead] = []

    for customer in customers:
        analysis = analyze_customer_risk(db, customer)
        priority_rows.append(
            PriorityCustomerRead(
                customer_id=analysis.customer_id,
                name=customer.name,
                risk_score=analysis.risk_score,
                risk_level=analysis.risk_level,
                top_reasons=analysis.reasons[:3],
                recommended_actions=analysis.recommended_actions[:4],
            )
        )

    priority_rows.sort(key=lambda row: row.risk_score, reverse=True)
    if limit is not None:
        return priority_rows[:limit]
    return priority_rows


def build_weekly_risk_report(db: Session) -> WeeklyRiskReport:
    priority_customers = get_priority_customers(db)
    total_customers = len(priority_customers)
    level_counts = Counter(customer.risk_level for customer in priority_customers)
    top_5_customers = priority_customers[:5]

    action_counter: Counter[str] = Counter()
    for customer in top_5_customers:
        action_counter.update(customer.recommended_actions)

    recommended_actions = [action for action, _ in action_counter.most_common(6)]
    executive_summary = _build_executive_summary(
        high_risk_count=level_counts.get("high", 0),
        priority_customers=top_5_customers,
    )

    return WeeklyRiskReport(
        total_customers=total_customers,
        high_risk_customers=level_counts.get("high", 0),
        medium_risk_customers=level_counts.get("medium", 0),
        low_risk_customers=level_counts.get("low", 0),
        top_5_customers=top_5_customers,
        recommended_actions=recommended_actions,
        executive_summary=executive_summary,
    )


def _build_executive_summary(
    high_risk_count: int,
    priority_customers: list[PriorityCustomerRead],
) -> str:
    if high_risk_count == 0:
        return (
            "This week, no customers require immediate attention. "
            "Continue monitoring support and payment signals."
        )

    reason_counter: Counter[str] = Counter()
    for customer in priority_customers:
        reason_counter.update(customer.top_reasons)
    main_drivers = [reason for reason, _ in reason_counter.most_common(2)]
    driver_text = " and ".join(main_drivers) if main_drivers else "business risk signals"
    return (
        f"This week, {high_risk_count} customers require immediate attention. "
        f"The main risk drivers are {driver_text}."
    )
