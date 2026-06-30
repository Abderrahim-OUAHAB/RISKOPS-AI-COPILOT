from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.rate_limit import rate_limit_by_ip
from app.models import Customer, RiskPrediction
from app.schemas import (
    CustomerRiskAnalysisResponse,
    CustomerRiskRead,
    PriorityCustomerRead,
    RiskExplanationResponse,
    RiskHistoryRead,
    RiskPredictionRequest,
    RiskPredictionResponse,
)
from app.services.model_service import (
    ModelNotTrainedError,
    ModelPredictionError,
)
from app.services.report_service import get_priority_customers
from app.services.risk_scoring_service import analyze_customer_risk

router = APIRouter(prefix="/risk", tags=["Risk"])


@router.post("/predict", response_model=RiskPredictionResponse)
def predict_risk(
    payload: RiskPredictionRequest,
    db: Session = Depends(get_db),
) -> RiskPredictionResponse:
    customer = (
        db.query(Customer)
        .filter(Customer.customer_external_id == payload.customer_id)
        .one_or_none()
    )
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found.",
        )

    try:
        analysis = analyze_customer_risk(
            db=db,
            customer=customer,
            language=payload.language,
        )
    except ModelNotTrainedError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except ModelPredictionError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not persist the prediction result.",
        ) from exc

    return RiskPredictionResponse(
        customer_id=analysis.customer_id,
        churn_probability=analysis.churn_probability,
        risk_score=analysis.risk_score,
        risk_level=analysis.risk_level,
        reasons=analysis.reasons,
        recommended_actions=analysis.recommended_actions,
        prediction_id=analysis.prediction_id,
        confidence=analysis.confidence,
        score_breakdown=analysis.score_breakdown,
        weighted_score_breakdown=analysis.weighted_score_breakdown,
        business_impact=analysis.business_impact,
        next_best_action=analysis.next_best_action,
        owner=analysis.owner,
        due_date=analysis.due_date,
        language=analysis.language,
    )


@router.post("/analyze-customer", response_model=CustomerRiskAnalysisResponse)
def analyze_customer(
    payload: RiskPredictionRequest,
    _: None = Depends(rate_limit_by_ip),
    db: Session = Depends(get_db),
) -> CustomerRiskAnalysisResponse:
    customer = _get_customer_or_404(db, payload.customer_id)

    try:
        analysis = analyze_customer_risk(
            db=db,
            customer=customer,
            language=payload.language,
        )
    except ModelNotTrainedError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except ModelPredictionError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not persist the RiskOps analysis.",
        ) from exc

    return CustomerRiskAnalysisResponse(**analysis.__dict__)


@router.get("/explain/{customer_id}", response_model=RiskExplanationResponse)
def explain_customer_risk(
    customer_id: str,
    language: str = Query(default="en"),
    _: None = Depends(rate_limit_by_ip),
    db: Session = Depends(get_db),
) -> RiskExplanationResponse:
    customer = _get_customer_or_404(db, customer_id)

    try:
        analysis = analyze_customer_risk(
            db=db,
            customer=customer,
            language=language,
        )
    except ModelNotTrainedError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except ModelPredictionError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not explain the customer risk.",
        ) from exc

    return RiskExplanationResponse(**analysis.__dict__)


@router.get("/priority-customers", response_model=list[PriorityCustomerRead])
def priority_customers(
    limit: int | None = Query(default=None, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[PriorityCustomerRead]:
    try:
        return get_priority_customers(db, limit=limit)
    except ModelNotTrainedError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except ModelPredictionError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get("/history", response_model=list[RiskHistoryRead])
def risk_history(
    customer_id: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[RiskPrediction]:
    statement = select(RiskPrediction).order_by(RiskPrediction.created_at.desc())
    if customer_id:
        statement = statement.where(RiskPrediction.customer_id == customer_id)
    statement = statement.limit(limit)
    return list(db.scalars(statement).all())


@router.get("/customers", response_model=list[CustomerRiskRead])
def list_customer_risks(db: Session = Depends(get_db)) -> list[CustomerRiskRead]:
    customers = list(db.scalars(select(Customer).order_by(Customer.customer_external_id)))
    try:
        for customer in customers:
            analyze_customer_risk(db=db, customer=customer)
    except ModelNotTrainedError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except ModelPredictionError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return [
        CustomerRiskRead(
            customer_id=customer.customer_external_id,
            name=customer.name,
            churn_probability=float(customer.churn_probability)
            if customer.churn_probability is not None
            else None,
            risk_score=float(customer.risk_score)
            if customer.risk_score is not None
            else None,
            risk_level=customer.risk_level,
        )
        for customer in customers
    ]


def _get_customer_or_404(db: Session, customer_id: str) -> Customer:
    customer = (
        db.query(Customer)
        .filter(Customer.customer_external_id == customer_id)
        .one_or_none()
    )
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found.",
        )
    return customer
