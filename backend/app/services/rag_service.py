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

UNKNOWN_ANSWERS = {
    "en": (
        "The available documents do not contain enough reliable information to answer. "
        "Upload or process a more relevant document, or verify that the selected document contains this topic."
    ),
    "fr": (
        "Les documents disponibles ne contiennent pas assez d'informations fiables pour repondre. "
        "Importez ou traitez un document plus pertinent, ou verifiez que le document selectionne contient ce sujet."
    ),
}


@dataclass
class DocumentProcessingResult:
    document_id: int
    status: str
    chunks_created: int


@dataclass
class RAGResult:
    answer: str
    sources: list[RAGSource]
    reasoning_summary: str = ""
    confidence: float = 0.0
    actions: list[str] | None = None
    missing_information: list[str] | None = None
    response_mode: str = "business"
    language: str = "en"


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
    language: str = "en",
    response_mode: str = "business",
) -> RAGResult:
    language = normalize_language(language)
    rewritten_question = rewrite_query(question, language)
    filters = [DocumentChunk.embedding.is_not(None)]
    if document_id is not None:
        filters.append(DocumentChunk.document_id == document_id)

    chunks_available = db.scalar(
        select(func.count()).select_from(DocumentChunk).where(*filters)
    )
    if not chunks_available:
        return _no_source_result(language=language, response_mode=response_mode)

    query_embedding = create_embeddings([rewritten_question])[0]
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
        document = chunk.document
        metadata = chunk.chunk_metadata or {}
        filename = document.filename if document is not None else metadata.get("filename")
        document_type = (
            document.document_type
            if document is not None
            else metadata.get("document_type")
        )
        sources.append(
            RAGSource(
                document_id=chunk.document_id,
                document_name=filename,
                filename=filename,
                document_type=document_type,
                chunk_id=chunk.id,
                chunk_index=chunk.chunk_index,
                content_preview=_preview_content(chunk.content),
                similarity_score=round(similarity_score, 4),
            )
        )

    if not sources:
        return _no_source_result(language=language, response_mode=response_mode)

    context_chunks = [
        f"[document_id={chunk.document_id}, chunk_id={chunk.id}]\n{chunk.content}"
        for chunk in source_chunks
    ]
    answer = generate_answer(
        question=question,
        context_chunks=context_chunks,
        language=language,
    )
    confidence = _estimate_confidence(sources)

    return RAGResult(
        answer=answer,
        sources=sources,
        reasoning_summary=_build_reasoning_summary(sources, language),
        confidence=confidence,
        actions=_suggest_actions(question, language),
        missing_information=[],
        response_mode=response_mode,
        language=language,
    )


def normalize_language(language: str | None) -> str:
    value = str(language or "en").strip().lower()
    return "fr" if value.startswith("fr") else "en"


def rewrite_query(question: str, language: str = "en") -> str:
    language = normalize_language(language)
    normalized = " ".join(question.split())
    lower_question = normalized.lower()
    expansions: list[str] = []

    if language == "fr":
        if any(term in lower_question for term in ["risque", "risques", "churn"]):
            expansions.extend(["risk score", "churn probability", "late payments", "support tickets"])
        if any(term in lower_question for term in ["action", "actions", "recommande"]):
            expansions.extend(["recommended action", "retention", "escalation"])
        if any(term in lower_question for term in ["client", "clients"]):
            expansions.extend(["customer", "account", "contract"])
    else:
        if any(term in lower_question for term in ["risk", "risks", "churn"]):
            expansions.extend(["risk score", "churn probability", "late payments", "support tickets"])
        if any(term in lower_question for term in ["action", "actions", "recommend"]):
            expansions.extend(["recommended action", "retention", "escalation"])
        if any(term in lower_question for term in ["customer", "client"]):
            expansions.extend(["customer", "account", "contract"])

    if not expansions:
        return normalized
    return f"{normalized}\nSearch context: {'; '.join(dict.fromkeys(expansions))}"


def _no_source_result(language: str, response_mode: str) -> RAGResult:
    missing = {
        "en": [
            "Relevant processed document chunks",
            "Clear customer, risk, payment or support evidence in the selected source",
        ],
        "fr": [
            "Passages de document traites et pertinents",
            "Preuves claires sur le client, le risque, les paiements ou le support dans la source selectionnee",
        ],
    }
    actions = {
        "en": [
            "Process the uploaded document before asking the question.",
            "Upload a small text-based PDF or CSV containing customer risk signals.",
            "Ask a question that matches the document content.",
        ],
        "fr": [
            "Traiter le document importe avant de poser la question.",
            "Importer un PDF textuel ou CSV leger contenant des signaux de risque client.",
            "Poser une question alignee avec le contenu du document.",
        ],
    }
    reasoning = {
        "en": "No reliable source chunk matched the question, so the system did not generate a speculative answer.",
        "fr": "Aucun chunk fiable ne correspond a la question, donc le systeme ne genere pas de reponse speculative.",
    }
    return RAGResult(
        answer=UNKNOWN_ANSWERS[language],
        sources=[],
        reasoning_summary=reasoning[language],
        confidence=0.0,
        actions=actions[language],
        missing_information=missing[language],
        response_mode=response_mode,
        language=language,
    )


def _estimate_confidence(sources: list[RAGSource]) -> float:
    if not sources:
        return 0.0
    scores = [source.similarity_score for source in sources]
    average_score = sum(scores) / len(scores)
    best_score = max(scores)
    confidence = (average_score * 0.7) + (best_score * 0.3)
    if len(sources) >= 3:
        confidence += 0.05
    return round(max(0.0, min(0.95, confidence)), 2)


def _build_reasoning_summary(sources: list[RAGSource], language: str) -> str:
    best_score = max((source.similarity_score for source in sources), default=0.0)
    if language == "fr":
        return (
            f"Reponse fondee sur {len(sources)} source(s) traitee(s), "
            f"avec une similarite maximale de {best_score:.2f}."
        )
    return (
        f"Answer grounded in {len(sources)} processed source(s), "
        f"with a top similarity score of {best_score:.2f}."
    )


def _suggest_actions(question: str, language: str) -> list[str]:
    lower_question = question.lower()
    asks_for_actions = any(
        term in lower_question
        for term in ["action", "actions", "recommend", "recommande", "faire", "prioriser"]
    )
    asks_for_risk = any(term in lower_question for term in ["risk", "risque", "churn", "priorit"])

    if language == "fr":
        actions = ["Verifier les chunks cites avant toute decision operationnelle."]
        if asks_for_risk:
            actions.append("Prioriser les clients avec retards de paiement ou tickets support repetes.")
        if asks_for_actions:
            actions.append("Transformer les constats en plan d'action client: contact, escalation ou retention.")
        return actions

    actions = ["Review the cited chunks before making an operational decision."]
    if asks_for_risk:
        actions.append("Prioritize customers with late payment or repeated support signals.")
    if asks_for_actions:
        actions.append("Turn the findings into a customer action plan: contact, escalation or retention.")
    return actions


def _preview_content(content: str, max_length: int = 240) -> str:
    normalized = " ".join(content.split())
    if len(normalized) <= max_length:
        return normalized

    return f"{normalized[: max_length - 3]}..."
