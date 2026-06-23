from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Customer
from app.schemas import (
    CustomerRiskRead,
    RiskPredictionRequest,
    RiskPredictionResponse,
)
from app.services.model_service import (
    ModelNotTrainedError,
    ModelPredictionError,
    predict_customer_risk,
)

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
        prediction = predict_customer_risk(db=db, customer=customer)
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

    return RiskPredictionResponse(**prediction)


@router.get("/customers", response_model=list[CustomerRiskRead])
def list_customer_risks(db: Session = Depends(get_db)) -> list[CustomerRiskRead]:
    customers = list(db.scalars(select(Customer).order_by(Customer.customer_external_id)))
    try:
        for customer in customers:
            predict_customer_risk(db=db, customer=customer)
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
