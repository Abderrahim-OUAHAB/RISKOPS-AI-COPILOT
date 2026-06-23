from app.models import Customer


def recommend_actions(customer: Customer, reasons: list[str], risk_score: int) -> list[str]:
    actions: list[str] = []

    if risk_score >= 70:
        actions.append("Contact customer within 48 hours")
        actions.append("Offer a retention discussion")
    elif risk_score >= 40:
        actions.append("Schedule a follow-up meeting")
    else:
        actions.append("Monitor customer for 7 days")

    if "Late payments detected" in reasons:
        actions.append("Review unpaid invoices")
    if "Many support tickets" in reasons:
        actions.append("Escalate recent support issues")
    if "Short customer tenure" in reasons:
        actions.append("Propose an onboarding check-in")
    if "Month-to-month contract" in reasons:
        actions.append("Offer a longer-term contract incentive")
    if "High value exposure" in reasons:
        actions.append("Assign account owner review")

    return _deduplicate(actions)


def _deduplicate(actions: list[str]) -> list[str]:
    seen = set()
    unique_actions = []
    for action in actions:
        if action not in seen:
            unique_actions.append(action)
            seen.add(action)
    return unique_actions
