from typing import Any

from pydantic import BaseModel, Field


class AgentAnalyzeRequest(BaseModel):
    question: str = Field(..., min_length=1)


class AgentAnalyzeResponse(BaseModel):
    answer: str
    selected_tool: str
    data: dict[str, Any]
    sources: list[dict[str, Any]] = []
