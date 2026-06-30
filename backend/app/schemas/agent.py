from typing import Any

from pydantic import BaseModel, Field


class AgentAnalyzeRequest(BaseModel):
    question: str = Field(..., min_length=1)
    language: str = "en"


class AgentAnalyzeResponse(BaseModel):
    answer: str
    selected_tool: str
    reasoning_summary: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    sources: list[dict[str, Any]] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    data: dict[str, Any]
    language: str = "en"
