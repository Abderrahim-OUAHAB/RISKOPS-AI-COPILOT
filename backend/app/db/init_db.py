from sqlalchemy import text

from app.db.base import Base
from app.db.session import engine
from app.models import Customer, Document, DocumentChunk  # noqa: F401


def init_db() -> None:
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    Base.metadata.create_all(bind=engine)
