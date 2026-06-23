from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import Document
from app.schemas import DocumentRead, DocumentUploadResponse
from app.services.file_storage import save_upload_file

router = APIRouter(prefix="/documents", tags=["Documents"])

ALLOWED_DOCUMENT_TYPES = {
    ".pdf": "pdf",
    ".csv": "csv",
}


def _get_document_type(filename: str | None) -> str:
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A filename is required.",
        )

    extension = Path(filename).suffix.lower()
    document_type = ALLOWED_DOCUMENT_TYPES.get(extension)
    if document_type is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Only PDF and CSV files are accepted.",
        )

    return document_type


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> DocumentUploadResponse:
    document_type = _get_document_type(file.filename)
    stored_path: Path | None = None

    try:
        stored_path, _ = save_upload_file(file, Path(settings.raw_data_dir))
        document = Document(
            filename=file.filename or stored_path.name,
            document_type=document_type,
            source_path=str(stored_path),
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        return DocumentUploadResponse(
            id=document.id,
            filename=document.filename,
            document_type=document.document_type,
            source_path=document.source_path,
            created_at=document.created_at,
            message="Document uploaded successfully.",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not store the uploaded file.",
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        if stored_path is not None:
            stored_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save document metadata.",
        ) from exc


@router.get("", response_model=list[DocumentRead])
def list_documents(db: Session = Depends(get_db)) -> list[Document]:
    statement = select(Document).order_by(Document.created_at.desc(), Document.id.desc())
    return list(db.scalars(statement).all())


@router.get("/{document_id}", response_model=DocumentRead)
def get_document(document_id: int, db: Session = Depends(get_db)) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    return document
