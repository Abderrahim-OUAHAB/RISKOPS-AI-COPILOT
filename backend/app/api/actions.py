from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit_by_ip
from app.db.session import get_db
from app.schemas import (
    ActionBoardResponse,
    ActionItemCreate,
    ActionItemResponse,
    ActionItemUpdate,
    ActionPlanResponse,
)
from app.services.action_service import (
    action_board_summary,
    complete_action,
    create_action,
    generate_action_plan,
    list_actions,
    sync_recommended_actions,
    update_action,
)
from app.services.model_service import ModelNotTrainedError, ModelPredictionError

router = APIRouter(prefix="/actions", tags=["Actions"])


@router.get("/plan", response_model=ActionPlanResponse)
def actions_plan(
    limit: int = Query(default=5, ge=1, le=25),
    language: str = Query(default="en"),
    db: Session = Depends(get_db),
) -> ActionPlanResponse:
    try:
        return generate_action_plan(db=db, language=language, limit=limit)
    except ModelNotTrainedError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except ModelPredictionError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post("/sync", response_model=list[ActionItemResponse])
def sync_actions(
    limit: int = Query(default=10, ge=1, le=50),
    language: str = Query(default="en"),
    _: None = Depends(rate_limit_by_ip),
    db: Session = Depends(get_db),
) -> list[ActionItemResponse]:
    try:
        return sync_recommended_actions(db=db, language=language, limit=limit)
    except ModelNotTrainedError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except ModelPredictionError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not sync actions.") from exc


@router.get("", response_model=list[ActionItemResponse])
def get_actions(
    status_filter: str | None = Query(default=None, alias="status"),
    owner: str | None = None,
    priority: str | None = None,
    customer_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[ActionItemResponse]:
    return list_actions(
        db=db,
        status=status_filter,
        owner=owner,
        priority=priority,
        customer_id=customer_id,
        limit=limit,
    )


@router.post("", response_model=ActionItemResponse, status_code=status.HTTP_201_CREATED)
def post_action(
    payload: ActionItemCreate,
    _: None = Depends(rate_limit_by_ip),
    db: Session = Depends(get_db),
) -> ActionItemResponse:
    try:
        return create_action(db=db, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create action.") from exc


@router.patch("/{action_id}", response_model=ActionItemResponse)
def patch_action(
    action_id: str,
    payload: ActionItemUpdate,
    _: None = Depends(rate_limit_by_ip),
    db: Session = Depends(get_db),
) -> ActionItemResponse:
    try:
        return update_action(db=db, action_id=action_id, payload=payload)
    except ValueError as exc:
        message = str(exc)
        http_status = status.HTTP_404_NOT_FOUND if "not found" in message.lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=http_status, detail=message) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not update action.") from exc


@router.post("/{action_id}/complete", response_model=ActionItemResponse)
def complete_tracked_action(
    action_id: str,
    _: None = Depends(rate_limit_by_ip),
    db: Session = Depends(get_db),
) -> ActionItemResponse:
    try:
        return complete_action(db=db, action_id=action_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not complete action.") from exc


@router.get("/board", response_model=ActionBoardResponse)
def get_action_board(
    language: str = Query(default="en"),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> ActionBoardResponse:
    return action_board_summary(db=db, language=language, limit=limit)
