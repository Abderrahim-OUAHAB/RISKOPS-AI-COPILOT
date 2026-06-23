from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RiskPredictionRequest(BaseModel):
    customer_id: str = Field(..., min_length=1)


class RiskPredictionResponse(BaseModel):
    customer_id: str
    churn_probability: float
    risk_score: int
    risk_level: str
    reasons: list[str]
    recommended_actions: list[str] = Field(default_factory=list)
    prediction_id: int | None = None


class CustomerRiskRead(BaseModel):
    customer_id: str | None
    name: str | None
    churn_probability: float | None
    risk_score: float | None
    risk_level: str | None


class CustomerRiskAnalysisResponse(BaseModel):
    customer_id: str
    risk_score: int
    risk_level: str
    churn_probability: float
    reasons: list[str]
    recommended_actions: list[str]
    prediction_id: int


class PriorityCustomerRead(BaseModel):
    customer_id: str
    name: str | None
    risk_score: int
    risk_level: str
    top_reasons: list[str]
    recommended_actions: list[str]


class RiskHistoryRead(BaseModel):
    id: int
    customer_id: str
    churn_probability: float
    risk_score: int
    risk_level: str
    reasons: list[str]
    recommended_actions: list[str]
    model_version: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
