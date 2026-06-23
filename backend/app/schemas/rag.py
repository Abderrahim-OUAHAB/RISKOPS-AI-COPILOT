from pydantic import BaseModel, Field


class RAGQuestion(BaseModel):
    question: str = Field(..., min_length=1)
    document_id: int | None = None


class RAGSource(BaseModel):
    document_id: int
    chunk_id: int
    content_preview: str
    similarity_score: float


class RAGAnswer(BaseModel):
    answer: str
    sources: list[RAGSource]
