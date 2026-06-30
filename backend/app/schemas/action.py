from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ActionItemBase(BaseModel):
    customer_id: str = Field(..., min_length=1)
    customer_name: str | None = None
    risk_level: str = "medium"
    priority: str = "medium"
    action_label: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)
    owner: str = Field(..., min_length=1)
    due_date: date | None = None
    status: str = "open"
    evidence_count: int = 0
    source: str = "manual"


class ActionItemCreate(ActionItemBase):
    action_id: str | None = None


class ActionItemUpdate(BaseModel):
    customer_name: str | None = None
    risk_level: str | None = None
    priority: str | None = None
    action_label: str | None = None
    reason: str | None = None
    owner: str | None = None
    due_date: date | None = None
    status: str | None = None
    evidence_count: int | None = None
    source: str | None = None


class ActionItemResponse(ActionItemBase):
    id: int
    action_id: str
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ActionBoardSummary(BaseModel):
    open_actions: int
    in_progress: int
    completed: int
    cancelled: int
    overdue: int
    high_priority: int


class ActionBoardResponse(BaseModel):
    summary: ActionBoardSummary
    actions: list[ActionItemResponse] = Field(default_factory=list)
    language: str = "en"
