import re
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Document, DocumentChunk


SIGNAL_KEYWORDS = {
    "payment_delay": [
        "late payment",
        "payment delay",
        "overdue payment",
        "retard de paiement",
        "paiement en retard",
        "en retard",
    ],
    "unpaid_invoice": [
        "unpaid invoice",
        "unpaid invoices",
        "invoice unpaid",
        "facture impayee",
        "factures impayees",
        "impaye",
        "impayee",
    ],
    "contract_penalty": [
        "penalty",
        "contract penalty",
        "late fee",
        "penalite",
        "penalite contractuelle",
    ],
    "contract_termination": [
        "termination",
        "contract termination",
        "cancel contract",
        "resiliation",
        "rupture de contrat",
    ],
    "support_escalation": [
        "support escalation",
        "escalation",
        "escalated",
        "escalade",
        "escalader",
    ],
    "complaint": [
        "complaint",
        "customer complaint",
        "reclamation",
        "plainte",
    ],
    "renewal_risk": [
        "renewal risk",
        "renewal at risk",
        "non renewal",
        "risque de renouvellement",
        "renouvellement a risque",
    ],
    "legal_risk": [
        "legal risk",
        "breach",
        "lawsuit",
        "legal dispute",
        "risque juridique",
        "litige",
        "rupture",
    ],
    "negative_sentiment": [
        "dissatisfied",
        "unhappy",
        "frustrated",
        "negative sentiment",
        "insatisfait",
        "mecontent",
        "frustre",
    ],
    "missing_information": [
        "missing information",
        "information missing",
        "incomplete",
        "information manquante",
        "incomplet",
    ],
}

SIGNAL_WEIGHTS = {
    "payment_delay": 35,
    "unpaid_invoice": 80,
    "contract_penalty": 75,
    "contract_termination": 85,
    "support_escalation": 60,
    "complaint": 45,
    "renewal_risk": 55,
    "legal_risk": 85,
    "negative_sentiment": 35,
    "missing_information": 20,
}

SEVERE_SIGNALS = {
    "unpaid_invoice",
    "contract_penalty",
    "contract_termination",
    "legal_risk",
}


@dataclass
class DocumentRiskResult:
    customer_id: str
    document_risk_score: int
    document_risk_level: str
    document_risk_signals: list[str] = field(default_factory=list)
    document_evidence: list[dict[str, Any]] = field(default_factory=list)
    linked_documents: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.2
    language: str = "en"


def calculate_document_risk(
    db: Session,
    customer_id: str,
    language: str = "en",
) -> DocumentRiskResult:
    language = normalize_language(language)
    linked_documents = find_linked_documents(db, customer_id)
    if not linked_documents:
        return DocumentRiskResult(
            customer_id=customer_id,
            document_risk_score=0,
            document_risk_level="low",
            document_risk_signals=[],
            document_evidence=[],
            linked_documents=[],
            confidence=0.2,
            language=language,
        )

    evidence: list[dict[str, Any]] = []
    signals: set[str] = set()

    for document in linked_documents:
        chunks = _chunks_for_document(db, document.id)
        if not chunks:
            document_signals = extract_document_signals(document.filename)
            for signal, keywords in document_signals.items():
                signals.add(signal)
                evidence.append(
                    _build_evidence(
                        document=document,
                        signal=signal,
                        keywords=keywords,
                        content=document.filename,
                    )
                )
            continue

        for chunk in chunks:
            if customer_id.lower() not in chunk.content.lower() and customer_id.lower() not in document.filename.lower():
                continue
            chunk_signals = extract_document_signals(chunk.content)
            for signal, keywords in chunk_signals.items():
                signals.add(signal)
                evidence.append(
                    _build_evidence(
                        document=document,
                        signal=signal,
                        keywords=keywords,
                        content=chunk.content,
                        chunk=chunk,
                    )
                )

    signal_list = sorted(signals, key=lambda item: SIGNAL_WEIGHTS.get(item, 0), reverse=True)
    score = _document_risk_score(signal_list)
    confidence = _document_confidence(len(linked_documents), len(evidence))

    return DocumentRiskResult(
        customer_id=customer_id,
        document_risk_score=score,
        document_risk_level=risk_level_from_score(score),
        document_risk_signals=signal_list,
        document_evidence=evidence[:10],
        linked_documents=[document_summary(document) for document in linked_documents],
        confidence=confidence,
        language=language,
    )


def find_linked_documents(db: Session, customer_id: str) -> list[Document]:
    normalized = customer_id.strip()
    if not normalized:
        return []

    documents: dict[int, Document] = {}
    filename_matches = db.scalars(
        select(Document).where(Document.filename.ilike(f"%{normalized}%"))
    ).all()
    for document in filename_matches:
        documents[document.id] = document

    chunk_matches = db.scalars(
        select(Document)
        .join(DocumentChunk)
        .where(DocumentChunk.content.ilike(f"%{normalized}%"))
        .distinct()
    ).all()
    for document in chunk_matches:
        documents[document.id] = document

    return sorted(documents.values(), key=lambda document: document.id, reverse=True)


def extract_document_signals(text: str) -> dict[str, list[str]]:
    lowered = normalize_text(text)
    detected: dict[str, list[str]] = {}
    for signal, keywords in SIGNAL_KEYWORDS.items():
        matches = [keyword for keyword in keywords if normalize_text(keyword) in lowered]
        if matches:
            detected[signal] = matches
    return detected


def document_summary(document: Document) -> dict[str, Any]:
    return {
        "document_id": document.id,
        "filename": document.filename,
        "document_type": document.document_type,
        "status": document.status,
        "processed_at": document.processed_at,
    }


def normalize_language(language: str | None) -> str:
    return "fr" if str(language or "en").strip().lower().startswith("fr") else "en"


def risk_level_from_score(score: int) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").lower()).strip()


def _chunks_for_document(db: Session, document_id: int) -> list[DocumentChunk]:
    return list(
        db.scalars(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
        ).all()
    )


def _document_risk_score(signals: list[str]) -> int:
    if not signals:
        return 0

    max_score = max(SIGNAL_WEIGHTS.get(signal, 0) for signal in signals)
    score = max_score + max(0, len(signals) - 1) * 8
    if any(signal in SEVERE_SIGNALS for signal in signals):
        score = max(score, 70)
    elif len(signals) == 1:
        score = max(20, min(score, 35))
    elif len(signals) >= 2:
        score = max(40, score)

    return int(max(0, min(100, round(score))))


def _document_confidence(document_count: int, evidence_count: int) -> float:
    if document_count == 0:
        return 0.2
    confidence = 0.45 + min(evidence_count, 5) * 0.08 + min(document_count, 3) * 0.05
    return round(max(0.2, min(0.9, confidence)), 2)


def _build_evidence(
    *,
    document: Document,
    signal: str,
    keywords: list[str],
    content: str,
    chunk: DocumentChunk | None = None,
) -> dict[str, Any]:
    return {
        "document_id": document.id,
        "filename": document.filename,
        "document_type": document.document_type,
        "chunk_id": chunk.id if chunk is not None else None,
        "chunk_index": chunk.chunk_index if chunk is not None else None,
        "signal": signal,
        "matched_keywords": keywords,
        "content_preview": _preview_content(content),
    }


def _preview_content(content: str, max_length: int = 260) -> str:
    normalized = " ".join(str(content or "").split())
    if len(normalized) <= max_length:
        return normalized
    return f"{normalized[: max_length - 3]}..."
