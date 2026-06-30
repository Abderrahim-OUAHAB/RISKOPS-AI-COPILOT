import hashlib
import re
from datetime import date, datetime
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.models import ActionItem, Customer
from app.schemas import (
    ActionBoardResponse,
    ActionBoardSummary,
    ActionItemCreate,
    ActionItemResponse,
    ActionItemUpdate,
    ActionPlanItem,
    ActionPlanResponse,
)
from app.services.document_intelligence_service import calculate_document_risk
from app.services.report_service import get_priority_customers

VALID_STATUSES = {"open", "in_progress", "completed", "cancelled"}
VALID_PRIORITIES = {"high", "medium", "low"}
VALID_SOURCES = {"risk_score", "document_risk", "manual", "agent"}


def normalize_language(language: str | None) -> str:
    return "fr" if str(language or "en").strip().lower().startswith("fr") else "en"


def generate_action_plan(
    db: Session,
    language: str = "en",
    limit: int = 5,
) -> ActionPlanResponse:
    language = normalize_language(language)
    priority_rows = get_priority_customers(db, limit=limit)
    actions: list[ActionPlanItem] = []

    for index, row in enumerate(priority_rows, start=1):
        document_risk = calculate_document_risk(
            db=db,
            customer_id=row.customer_id,
            language=language,
        )
        action_label = row.next_best_action or (
            row.recommended_actions[0] if row.recommended_actions else _default_action(language)
        )
        reason = row.top_reasons[0] if row.top_reasons else _default_reason(language)
        priority = priority_from_level(row.risk_level)
        actions.append(
            ActionPlanItem(
                action_id=_stable_action_id(row.customer_id, action_label),
                customer_id=row.customer_id,
                customer_name=row.name,
                risk_level=row.risk_level,
                priority=priority,
                action_label=action_label,
                reason=reason,
                owner=row.owner or "Customer Success Manager",
                due_date=row.due_date or "",
                evidence_count=len(document_risk.document_evidence),
                status="open",
            )
        )

    summary = (
        f"{len(actions)} priority actions generated from customer risk and document evidence."
        if language == "en"
        else f"{len(actions)} actions prioritaires generees a partir du risque client et des preuves documentaires."
    )
    return ActionPlanResponse(summary=summary, actions=actions, language=language)


def sync_recommended_actions(
    db: Session,
    language: str = "en",
    limit: int = 10,
) -> list[ActionItem]:
    plan = generate_action_plan(db=db, language=language, limit=limit)
    synced: list[ActionItem] = []

    for item in plan.actions:
        existing = _find_open_duplicate(
            db=db,
            customer_id=item.customer_id,
            action_label=item.action_label,
        )
        if existing is None:
            existing = get_action_or_none(db, item.action_id)
        if existing is None:
            existing = ActionItem(
                action_id=item.action_id,
                customer_id=item.customer_id,
                customer_name=item.customer_name,
                risk_level=item.risk_level,
                priority=item.priority,
                action_label=item.action_label,
                reason=item.reason,
                owner=item.owner,
                due_date=_parse_date(item.due_date),
                status="open",
                evidence_count=item.evidence_count,
                source="document_risk" if item.evidence_count > 0 else "risk_score",
            )
            db.add(existing)
        else:
            existing.customer_name = item.customer_name
            existing.risk_level = item.risk_level
            existing.priority = item.priority
            existing.reason = item.reason
            existing.owner = item.owner
            existing.due_date = _parse_date(item.due_date)
            existing.evidence_count = item.evidence_count
            existing.source = "document_risk" if item.evidence_count > 0 else "risk_score"
        synced.append(existing)

    db.commit()
    for item in synced:
        db.refresh(item)
    return synced


def list_actions(
    db: Session,
    *,
    status: str | None = None,
    owner: str | None = None,
    priority: str | None = None,
    customer_id: str | None = None,
    limit: int = 100,
) -> list[ActionItem]:
    statement = select(ActionItem).order_by(
        ActionItem.due_date.asc().nulls_last(),
        ActionItem.created_at.desc(),
    )
    if status:
        statement = statement.where(ActionItem.status == status)
    if owner:
        statement = statement.where(ActionItem.owner.ilike(f"%{owner}%"))
    if priority:
        statement = statement.where(ActionItem.priority == priority)
    if customer_id:
        statement = statement.where(ActionItem.customer_id == customer_id)
    statement = statement.limit(limit)
    return list(db.scalars(statement).all())


def create_action(db: Session, payload: ActionItemCreate) -> ActionItem:
    _validate_status(payload.status)
    _validate_priority(payload.priority)
    _validate_source(payload.source)
    action = ActionItem(
        action_id=payload.action_id or _stable_action_id(payload.customer_id, payload.action_label),
        customer_id=payload.customer_id,
        customer_name=payload.customer_name,
        risk_level=payload.risk_level,
        priority=payload.priority,
        action_label=payload.action_label,
        reason=payload.reason,
        owner=payload.owner,
        due_date=payload.due_date,
        status=payload.status,
        evidence_count=payload.evidence_count,
        source=payload.source,
        completed_at=datetime.utcnow() if payload.status == "completed" else None,
    )
    db.add(action)
    db.commit()
    db.refresh(action)
    return action


def update_action(db: Session, action_id: str, payload: ActionItemUpdate) -> ActionItem:
    action = get_action_or_none(db, action_id)
    if action is None:
        raise ValueError("Action not found.")

    update_data = payload.model_dump(exclude_unset=True)
    if "status" in update_data and update_data["status"] is not None:
        _validate_status(update_data["status"])
        if update_data["status"] == "completed" and action.completed_at is None:
            action.completed_at = datetime.utcnow()
        elif update_data["status"] != "completed":
            action.completed_at = None
    if "priority" in update_data and update_data["priority"] is not None:
        _validate_priority(update_data["priority"])
    if "source" in update_data and update_data["source"] is not None:
        _validate_source(update_data["source"])

    for key, value in update_data.items():
        setattr(action, key, value)

    db.commit()
    db.refresh(action)
    return action


def complete_action(db: Session, action_id: str) -> ActionItem:
    action = get_action_or_none(db, action_id)
    if action is None:
        raise ValueError("Action not found.")
    action.status = "completed"
    action.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(action)
    return action


def get_action_or_none(db: Session, action_id: str) -> ActionItem | None:
    return db.scalar(select(ActionItem).where(ActionItem.action_id == action_id))


def action_board_summary(
    db: Session,
    language: str = "en",
    limit: int = 100,
) -> ActionBoardResponse:
    actions = list_actions(db, limit=limit)
    today = date.today()
    summary = ActionBoardSummary(
        open_actions=sum(1 for action in actions if action.status == "open"),
        in_progress=sum(1 for action in actions if action.status == "in_progress"),
        completed=sum(1 for action in actions if action.status == "completed"),
        cancelled=sum(1 for action in actions if action.status == "cancelled"),
        overdue=sum(
            1
            for action in actions
            if action.due_date is not None
            and action.due_date < today
            and action.status in {"open", "in_progress"}
        ),
        high_priority=sum(1 for action in actions if action.priority == "high"),
    )
    return ActionBoardResponse(
        summary=summary,
        actions=[ActionItemResponse.model_validate(action) for action in actions],
        language=normalize_language(language),
    )


def priority_from_level(risk_level: str | None) -> str:
    if risk_level == "high":
        return "high"
    if risk_level == "medium":
        return "medium"
    return "low"


def _find_open_duplicate(
    db: Session,
    customer_id: str,
    action_label: str,
) -> ActionItem | None:
    return db.scalar(
        select(ActionItem).where(
            and_(
                ActionItem.customer_id == customer_id,
                func.lower(ActionItem.action_label) == action_label.lower(),
                or_(
                    ActionItem.status == "open",
                    ActionItem.status == "in_progress",
                ),
            )
        )
    )


def _stable_action_id(customer_id: str, action_label: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", f"{customer_id}-{action_label}".lower()).strip("-")
    digest = hashlib.sha1(f"{customer_id}|{action_label}".encode("utf-8")).hexdigest()[:8]
    return f"act-{slug[:42]}-{digest}"


def _parse_date(value: str | date | None) -> date | None:
    if value is None or isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _validate_status(status: str) -> None:
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status. Expected one of: {', '.join(sorted(VALID_STATUSES))}.")


def _validate_priority(priority: str) -> None:
    if priority not in VALID_PRIORITIES:
        raise ValueError(f"Invalid priority. Expected one of: {', '.join(sorted(VALID_PRIORITIES))}.")


def _validate_source(source: str) -> None:
    if source not in VALID_SOURCES:
        raise ValueError(f"Invalid source. Expected one of: {', '.join(sorted(VALID_SOURCES))}.")


def _default_action(language: str) -> str:
    return "Review customer risk" if language == "en" else "Revoir le risque client"


def _default_reason(language: str) -> str:
    return "Risk score requires review." if language == "en" else "Le score de risque necessite une revue."
