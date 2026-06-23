from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Document
from app.schemas import RAGAnswer, RAGQuestion
from app.services.embedding_service import OpenAIConfigurationError, OpenAIServiceError
from app.services.rag_service import answer_question

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.post("/ask", response_model=RAGAnswer)
def ask_rag_question(
    payload: RAGQuestion,
    db: Session = Depends(get_db),
) -> RAGAnswer:
    if payload.document_id is not None and db.get(Document, payload.document_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    try:
        result = answer_question(
            db=db,
            question=payload.question,
            document_id=payload.document_id,
        )
    except OpenAIConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except OpenAIServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not search document chunks.",
        ) from exc

    return RAGAnswer(answer=result.answer, sources=result.sources)
