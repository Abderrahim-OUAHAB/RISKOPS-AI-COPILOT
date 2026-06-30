from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.rate_limit import rate_limit_by_ip
from app.models import Customer, RiskPrediction
from app.schemas import (
    ActionPlanResponse,
    Client360Response,
    CustomerRiskAnalysisResponse,
    CustomerRiskRead,
    DocumentRiskResponse,
    PriorityCustomerRead,
    RiskExplanationResponse,
    RiskHistoryRead,
    RiskPredictionRequest,
    RiskPredictionResponse,
)
from app.services.action_service import generate_action_plan, list_actions
from app.services.document_intelligence_service import calculate_document_risk
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
        document_risk_score=analysis.document_risk_score,
        document_risk_level=analysis.document_risk_level,
        document_risk_signals=analysis.document_risk_signals,
        document_evidence=analysis.document_evidence,
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


@router.get("/document-risk/{customer_id}", response_model=DocumentRiskResponse)
def document_risk(
    customer_id: str,
    language: str = Query(default="en"),
    _: None = Depends(rate_limit_by_ip),
    db: Session = Depends(get_db),
) -> DocumentRiskResponse:
    _get_customer_or_404(db, customer_id)
    result = calculate_document_risk(db=db, customer_id=customer_id, language=language)
    return DocumentRiskResponse(**result.__dict__)


@router.get("/client-360/{customer_id}", response_model=Client360Response)
def client_360(
    customer_id: str,
    language: str = Query(default="en"),
    _: None = Depends(rate_limit_by_ip),
    db: Session = Depends(get_db),
) -> Client360Response:
    customer = _get_customer_or_404(db, customer_id)

    try:
        analysis = analyze_customer_risk(db=db, customer=customer, language=language)
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
            detail="Could not build Client 360 view.",
        ) from exc

    document_risk_result = calculate_document_risk(
        db=db,
        customer_id=customer_id,
        language=language,
    )
    predictions = list(
        db.scalars(
            select(RiskPrediction)
            .where(RiskPrediction.customer_id == customer_id)
            .order_by(RiskPrediction.created_at.desc())
            .limit(5)
        ).all()
    )

    return Client360Response(
        customer=_customer_payload(customer),
        latest_risk_analysis=analysis.__dict__,
        risk_explanation=analysis.__dict__,
        document_risk=document_risk_result.__dict__,
        linked_documents=document_risk_result.linked_documents,
        recent_predictions=[_prediction_payload(prediction) for prediction in predictions],
        tracked_actions=[_action_payload(action) for action in list_actions(db, customer_id=customer_id, limit=50)],
        recommended_actions=analysis.recommended_actions,
        next_best_action=analysis.next_best_action,
        owner=analysis.owner,
        due_date=analysis.due_date,
        confidence=analysis.confidence,
        language=analysis.language,
    )


@router.get("/action-plan", response_model=ActionPlanResponse)
def action_plan(
    limit: int = Query(default=5, ge=1, le=25),
    language: str = Query(default="en"),
    db: Session = Depends(get_db),
) -> ActionPlanResponse:
    try:
        return generate_action_plan(db=db, language=language, limit=limit)
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


def _customer_payload(customer: Customer) -> dict:
    return {
        "id": customer.id,
        "customer_id": customer.customer_external_id,
        "name": customer.name,
        "segment": customer.segment,
        "monthly_spend": float(customer.monthly_spend) if customer.monthly_spend is not None else None,
        "tenure": customer.tenure,
        "monthly_charges": float(customer.monthly_charges) if customer.monthly_charges is not None else None,
        "total_charges": float(customer.total_charges) if customer.total_charges is not None else None,
        "contract_type": customer.contract_type,
        "support_tickets": customer.support_tickets,
        "late_payments": customer.late_payments,
        "support_ticket_count": customer.support_ticket_count,
        "unpaid_invoice_count": customer.unpaid_invoice_count,
        "risk_score": float(customer.risk_score) if customer.risk_score is not None else None,
        "risk_level": customer.risk_level,
    }


def _prediction_payload(prediction: RiskPrediction) -> dict:
    return {
        "id": prediction.id,
        "customer_id": prediction.customer_id,
        "churn_probability": float(prediction.churn_probability),
        "risk_score": prediction.risk_score,
        "risk_level": prediction.risk_level,
        "reasons": prediction.reasons,
        "recommended_actions": prediction.recommended_actions,
        "model_version": prediction.model_version,
        "created_at": prediction.created_at,
    }


def _action_payload(action: object) -> dict:
    return {
        "action_id": getattr(action, "action_id", None),
        "customer_id": getattr(action, "customer_id", None),
        "customer_name": getattr(action, "customer_name", None),
        "risk_level": getattr(action, "risk_level", None),
        "priority": getattr(action, "priority", None),
        "action_label": getattr(action, "action_label", None),
        "reason": getattr(action, "reason", None),
        "owner": getattr(action, "owner", None),
        "due_date": getattr(action, "due_date", None),
        "status": getattr(action, "status", None),
        "evidence_count": getattr(action, "evidence_count", None),
        "source": getattr(action, "source", None),
        "created_at": getattr(action, "created_at", None),
        "updated_at": getattr(action, "updated_at", None),
        "completed_at": getattr(action, "completed_at", None),
    }


def _priority_from_level(risk_level: str | None) -> str:
    if risk_level == "high":
        return "P1"
    if risk_level == "medium":
        return "P2"
    return "P3"
