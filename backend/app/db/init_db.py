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
        customer_columns = {
            "tenure": "INTEGER",
            "monthly_charges": "NUMERIC",
            "total_charges": "NUMERIC",
            "contract_type": "TEXT",
            "support_tickets": "INTEGER NOT NULL DEFAULT 0",
            "late_payments": "INTEGER NOT NULL DEFAULT 0",
            "churn": "INTEGER",
            "risk_level": "TEXT",
            "updated_at": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
        }
        for column_name, column_type in customer_columns.items():
            connection.execute(
                text(
                    f"""
                    ALTER TABLE customers
                    ADD COLUMN IF NOT EXISTS {column_name} {column_type}
                    """
                )
            )
        connection.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS ix_customers_customer_external_id
                ON customers (customer_external_id)
                """
            )
        )
