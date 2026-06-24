from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import AgentAnalyzeRequest, AgentAnalyzeResponse
from app.services.llm_observability_service import trace_llm_call
from app.services.model_service import ModelNotTrainedError, ModelPredictionError
from app.services.riskops_agent import analyze_with_agent

router = APIRouter(prefix="/agent", tags=["Agent"])


@router.post("/analyze", response_model=AgentAnalyzeResponse)
def analyze_question(
    payload: AgentAnalyzeRequest,
    db: Session = Depends(get_db),
) -> AgentAnalyzeResponse:
    with trace_llm_call(operation="agent", question=payload.question) as trace:
        try:
            result = analyze_with_agent(db=db, question=payload.question)
            trace["selected_tool"] = result.get("selected_tool")
            trace["number_of_sources"] = len(result.get("sources", []))
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
                detail="Could not run RiskOps agent workflow.",
            ) from exc

        return AgentAnalyzeResponse(**result)
