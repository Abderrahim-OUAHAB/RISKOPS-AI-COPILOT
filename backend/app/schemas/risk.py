from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RiskPredictionRequest(BaseModel):
    customer_id: str = Field(..., min_length=1)
    language: str = "en"


class RiskScoreBreakdown(BaseModel):
    ml: float
    payment: float
    support: float
    contract: float
    document: float
    trend: float
    recency: float


class RiskPredictionResponse(BaseModel):
    customer_id: str
    churn_probability: float
    risk_score: int
    risk_level: str
    reasons: list[str]
    recommended_actions: list[str] = Field(default_factory=list)
    prediction_id: int | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    score_breakdown: RiskScoreBreakdown | None = None
    weighted_score_breakdown: RiskScoreBreakdown | None = None
    business_impact: str | None = None
    next_best_action: str | None = None
    owner: str | None = None
    due_date: str | None = None
    language: str = "en"


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
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    score_breakdown: RiskScoreBreakdown
    weighted_score_breakdown: RiskScoreBreakdown
    business_impact: str
    next_best_action: str
    owner: str
    due_date: str
    language: str = "en"


class PriorityCustomerRead(BaseModel):
    customer_id: str
    name: str | None
    risk_score: int
    risk_level: str
    top_reasons: list[str]
    recommended_actions: list[str]
    confidence: float | None = None
    next_best_action: str | None = None
    owner: str | None = None
    due_date: str | None = None


class RiskExplanationResponse(CustomerRiskAnalysisResponse):
    pass


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
