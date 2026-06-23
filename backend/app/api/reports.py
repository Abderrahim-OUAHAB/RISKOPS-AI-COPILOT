from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import WeeklyRiskReport
from app.services.model_service import ModelNotTrainedError, ModelPredictionError
from app.services.report_service import build_weekly_risk_report

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/weekly-risk", response_model=WeeklyRiskReport)
def weekly_risk_report(db: Session = Depends(get_db)) -> WeeklyRiskReport:
    try:
        return build_weekly_risk_report(db)
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
            detail="Could not build weekly risk report.",
        ) from exc
