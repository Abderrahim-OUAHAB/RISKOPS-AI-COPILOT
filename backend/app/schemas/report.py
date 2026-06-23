from pydantic import BaseModel

from app.schemas.risk import PriorityCustomerRead


class WeeklyRiskReport(BaseModel):
    total_customers: int
    high_risk_customers: int
    medium_risk_customers: int
    low_risk_customers: int
    top_5_customers: list[PriorityCustomerRead]
    recommended_actions: list[str]
    executive_summary: str
