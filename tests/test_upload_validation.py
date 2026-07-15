from io import BytesIO

from fastapi import UploadFile
from sqlalchemy.exc import SQLAlchemyError

import app.api.customers as customers_api
from app.services.file_storage import save_upload_file


class FakeDb:
    def __init__(self):
        self.rollback_called = False

    def rollback(self):
        self.rollback_called = True


def test_supported_customer_csv_upload(client_factory, monkeypatch):
    monkeypatch.setattr(customers_api, "import_customers_from_csv", lambda _file, _db: 1)
    db = FakeDb()

    with client_factory(db) as client:
        response = client.post(
            "/customers/import",
            files={"file": ("customers.csv", b"customer_id,name\nsample,Alpha\n", "text/csv")},
        )

    assert response.status_code == 200
    assert response.json()["imported_count"] == 1


def test_malformed_customer_csv_returns_400(client_factory):
    with client_factory(FakeDb()) as client:
        response = client.post(
            "/customers/import",
            files={"file": ("customers.csv", b"wrong,columns\n1,2\n", "text/csv")},
        )

    assert response.status_code == 400
    assert "Missing required columns" in response.json()["detail"]


def test_unsupported_customer_file_type_returns_400(client_factory):
    with client_factory(FakeDb()) as client:
        response = client.post(
            "/customers/import",
            files={"file": ("customers.txt", b"data", "text/plain")},
        )

    assert response.status_code == 400


def test_empty_customer_csv_returns_400(client_factory):
    with client_factory(FakeDb()) as client:
        response = client.post(
            "/customers/import",
            files={"file": ("customers.csv", b"", "text/csv")},
        )

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_oversized_customer_csv_returns_400(client_factory, monkeypatch):
    monkeypatch.setattr(customers_api.settings, "max_upload_size_mb", 1)

    with client_factory(FakeDb()) as client:
        response = client.post(
            "/customers/import",
            files={"file": ("customers.csv", b"x" * (1024 * 1024 + 1), "text/csv")},
        )

    assert response.status_code == 400
    assert "too large" in response.json()["detail"].lower()


def test_unsafe_filename_is_sanitized_inside_target_directory(tmp_path):
    upload = UploadFile(filename="../../outside.csv", file=BytesIO(b"a,b\n1,2\n"))

    stored_path, _ = save_upload_file(upload, tmp_path, max_size_bytes=1024)

    assert stored_path.parent == tmp_path
    assert ".." not in stored_path.name
    assert stored_path.exists()


def test_customer_import_rolls_back_on_database_failure(client_factory, monkeypatch):
    db = FakeDb()
    monkeypatch.setattr(
        customers_api,
        "import_customers_from_csv",
        lambda _file, _db: (_ for _ in ()).throw(SQLAlchemyError("failure")),
    )

    with client_factory(db) as client:
        response = client.post(
            "/customers/import",
            files={"file": ("customers.csv", b"customer_id,name\nsample,Alpha\n", "text/csv")},
        )

    assert response.status_code == 500
    assert db.rollback_called is True
