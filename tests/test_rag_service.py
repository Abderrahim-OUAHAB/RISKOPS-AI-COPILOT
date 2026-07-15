from types import SimpleNamespace

import pytest

import app.api.rag as rag_api
import app.services.rag_service as rag_service
from app.services.embedding_service import OpenAIServiceError


class FakeRagSession:
    def __init__(self, rows=None, available=1):
        self.rows = rows or []
        self.available = available

    def scalar(self, _statement):
        return self.available

    def execute(self, _statement):
        return SimpleNamespace(all=lambda: self.rows)

    def get(self, _model, _identifier):
        return None


def source_row(distance: float):
    document = SimpleNamespace(filename="risk.csv", document_type="csv")
    chunk = SimpleNamespace(
        id=9,
        document_id=3,
        chunk_index=0,
        content="Account Alpha has repeated support issues and late payments.",
        chunk_metadata={},
        document=document,
    )
    return chunk, distance


def test_relevant_retrieval_returns_answer_and_sources(monkeypatch):
    monkeypatch.setattr(rag_service, "create_embeddings", lambda _texts: [[0.1] * 1536])
    monkeypatch.setattr(rag_service, "generate_answer", lambda **_kwargs: "Grounded answer [document_id=3, chunk_id=9]")

    result = rag_service.answer_question(
        FakeRagSession(rows=[source_row(0.1)]),
        "What are the risks?",
    )

    assert result.answer.startswith("Grounded answer")
    assert len(result.sources) == 1
    assert result.sources[0].chunk_id == 9


def test_empty_retrieval_returns_refusal_without_openai(monkeypatch):
    monkeypatch.setattr(
        rag_service,
        "create_embeddings",
        lambda _texts: pytest.fail("embeddings should not be called"),
    )

    result = rag_service.answer_question(FakeRagSession(available=0), "Unknown topic")

    assert result.confidence == 0.0
    assert result.sources == []
    assert "enough reliable information" in result.answer


def test_irrelevant_retrieval_does_not_generate_answer(monkeypatch):
    monkeypatch.setattr(rag_service, "create_embeddings", lambda _texts: [[0.1] * 1536])
    monkeypatch.setattr(
        rag_service,
        "generate_answer",
        lambda **_kwargs: pytest.fail("generation should not be called"),
    )

    result = rag_service.answer_question(
        FakeRagSession(rows=[source_row(0.95)]),
        "Unrelated topic",
    )

    assert result.sources == []
    assert result.confidence == 0.0


def test_openai_failure_maps_to_502(client_factory, monkeypatch):
    monkeypatch.setattr(
        rag_api,
        "answer_question",
        lambda **_kwargs: (_ for _ in ()).throw(OpenAIServiceError("OpenAI request failed")),
    )

    with client_factory(FakeRagSession()) as client:
        response = client.post("/rag/ask", json={"question": "Document question"})

    assert response.status_code == 502
    assert response.json()["detail"] == "OpenAI request failed"
