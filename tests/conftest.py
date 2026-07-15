from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
APP_ROOT = PROJECT_ROOT if (PROJECT_ROOT / "app").is_dir() else BACKEND_ROOT
sys.path.insert(0, str(APP_ROOT))

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["OPENAI_API_KEY"] = "test-placeholder"
os.environ["ENABLE_LANGFUSE"] = "false"

from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
import app.main as main_module  # noqa: E402


@pytest.fixture
def client_factory(monkeypatch):
    clients: list[TestClient] = []
    monkeypatch.setattr(main_module, "init_db", lambda: None)

    @contextmanager
    def factory(db) -> Iterator[TestClient]:
        app.dependency_overrides[get_db] = lambda: db
        client = TestClient(app)
        clients.append(client)
        try:
            with client:
                yield client
        finally:
            app.dependency_overrides.clear()

    yield factory

    for client in clients:
        client.close()
    app.dependency_overrides.clear()
