from pydantic import BaseModel, Field


class RiskPredictionRequest(BaseModel):
    customer_id: str = Field(..., min_length=1)


class RiskPredictionResponse(BaseModel):
    customer_id: str
    churn_probability: float
    risk_score: int
    risk_level: str
    reasons: list[str]


class CustomerRiskRead(BaseModel):
    customer_id: str | None
    name: str | None
    churn_probability: float | None
    risk_score: float | None
    risk_level: str | None
