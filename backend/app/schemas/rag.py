from pydantic import BaseModel, Field


class RAGQuestion(BaseModel):
    question: str = Field(..., min_length=1)
    document_id: int | None = None
    language: str = "en"
    response_mode: str = "business"


class RAGSource(BaseModel):
    document_id: int
    document_name: str | None = None
    filename: str | None = None
    document_type: str | None = None
    chunk_id: int
    chunk_index: int | None = None
    content_preview: str
    similarity_score: float


class RAGAnswer(BaseModel):
    answer: str
    reasoning_summary: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    sources: list[RAGSource] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    response_mode: str = "business"
