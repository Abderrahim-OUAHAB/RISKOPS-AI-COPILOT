from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Document, DocumentChunk
from app.schemas import RAGSource
from app.services.chunking import chunk_text
from app.services.embedding_service import create_embeddings, generate_answer
from app.services.text_extraction import extract_text_from_document

UNKNOWN_ANSWER = (
    "Je ne sais pas avec les sources disponibles. "
    "Le document doit etre traite ou contenir des passages suffisamment pertinents."
)


@dataclass
class DocumentProcessingResult:
    document_id: int
    status: str
    chunks_created: int


@dataclass
class RAGResult:
    answer: str
    sources: list[RAGSource]


class DocumentProcessingError(Exception):
    pass


def process_document(db: Session, document: Document) -> DocumentProcessingResult:
    document.status = "processing"
    document.processed_at = None
    db.commit()
    db.refresh(document)

    try:
        text = extract_text_from_document(document)
        chunks = chunk_text(text)
        if not chunks:
            raise DocumentProcessingError("No chunks were created from the document.")

        embeddings = create_embeddings(chunks)
        if len(embeddings) != len(chunks):
            raise DocumentProcessingError("Embedding count does not match chunk count.")

        db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
        total_chunks = len(chunks)
        for chunk_index, (content, embedding) in enumerate(zip(chunks, embeddings)):
            db.add(
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=chunk_index,
                    content=content,
                    embedding=embedding,
                    chunk_metadata={
                        "filename": document.filename,
                        "document_type": document.document_type,
                        "total_chunks": total_chunks,
                        "content_length": len(content),
                    },
                )
            )

        document.status = "processed"
        document.processed_at = datetime.utcnow()
        db.commit()

        return DocumentProcessingResult(
            document_id=document.id,
            status=document.status,
            chunks_created=total_chunks,
        )
    except Exception:
        db.rollback()
        failed_document = db.get(Document, document.id)
        if failed_document is not None:
            failed_document.status = "processing_failed"
            failed_document.processed_at = None
            db.commit()
        raise


def answer_question(
    db: Session,
    question: str,
    document_id: int | None = None,
) -> RAGResult:
    filters = [DocumentChunk.embedding.is_not(None)]
    if document_id is not None:
        filters.append(DocumentChunk.document_id == document_id)

    chunks_available = db.scalar(
        select(func.count()).select_from(DocumentChunk).where(*filters)
    )
    if not chunks_available:
        return RAGResult(answer=UNKNOWN_ANSWER, sources=[])

    query_embedding = create_embeddings([question])[0]
    distance = DocumentChunk.embedding.cosine_distance(query_embedding).label("distance")
    statement = (
        select(DocumentChunk, distance)
        .where(*filters)
        .order_by(distance)
        .limit(settings.rag_top_k)
    )

    rows = db.execute(statement).all()
    source_chunks: list[DocumentChunk] = []
    sources: list[RAGSource] = []

    for chunk, distance_value in rows:
        similarity_score = max(0.0, min(1.0, 1.0 - float(distance_value)))
        if similarity_score < settings.rag_similarity_threshold:
            continue

        source_chunks.append(chunk)
        sources.append(
            RAGSource(
                document_id=chunk.document_id,
                chunk_id=chunk.id,
                content_preview=_preview_content(chunk.content),
                similarity_score=round(similarity_score, 4),
            )
        )

    if not sources:
        return RAGResult(answer=UNKNOWN_ANSWER, sources=[])

    context_chunks = [
        f"[document_id={chunk.document_id}, chunk_id={chunk.id}]\n{chunk.content}"
        for chunk in source_chunks
    ]
    answer = generate_answer(question=question, context_chunks=context_chunks)

    return RAGResult(answer=answer, sources=sources)


def _preview_content(content: str, max_length: int = 240) -> str:
    normalized = " ".join(content.split())
    if len(normalized) <= max_length:
        return normalized

    return f"{normalized[: max_length - 3]}..."
