from sqlalchemy import text

from app.db.base import Base
from app.db.session import engine
from app.models import Customer, Document, DocumentChunk  # noqa: F401


def init_db() -> None:
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    Base.metadata.create_all(bind=engine)

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                ALTER TABLE documents
                ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'uploaded'
                """
            )
        )
        connection.execute(
            text(
                """
                ALTER TABLE documents
                ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS ix_documents_status
                ON documents (status)
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS ix_document_chunks_document_id
                ON document_chunks (document_id)
                """
            )
        )
