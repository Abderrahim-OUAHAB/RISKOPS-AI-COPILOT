from llama_index.core.node_parser import SentenceSplitter

from app.core.config import settings


def chunk_text(text: str) -> list[str]:
    splitter = SentenceSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    chunks = [chunk.strip() for chunk in splitter.split_text(text) if chunk.strip()]
    return chunks
