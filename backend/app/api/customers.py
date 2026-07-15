from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.rate_limit import rate_limit_by_ip
from app.db.session import get_db
from app.models import Customer
from app.schemas import CustomerImportResponse, CustomerRead
from app.services.customer_import_service import (
    CustomerImportError,
    import_customers_from_csv,
)
from app.services.file_storage import copy_upload_to_temporary_file

router = APIRouter(prefix="/customers", tags=["Customers"])

ALLOWED_CSV_CONTENT_TYPES = {
    "application/csv",
    "application/octet-stream",
    "application/vnd.ms-excel",
    "text/csv",
    "text/plain",
}


@router.post("/import", response_model=CustomerImportResponse)
def import_customers(
    file: UploadFile = File(...),
    _: None = Depends(rate_limit_by_ip),
    db: Session = Depends(get_db),
) -> CustomerImportResponse:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are accepted.",
        )
    if file.content_type and file.content_type.lower() not in ALLOWED_CSV_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported CSV content type.",
        )

    temporary_file = None
    try:
        temporary_file, _ = copy_upload_to_temporary_file(
            file,
            max_size_bytes=settings.max_upload_size_bytes,
        )
        imported_count = import_customers_from_csv(temporary_file, db)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except CustomerImportError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not import customers into PostgreSQL.",
        ) from exc
    finally:
        if temporary_file is not None:
            temporary_file.close()

    return CustomerImportResponse(
        imported_count=imported_count,
        message="Customers imported successfully.",
    )


@router.get("", response_model=list[CustomerRead])
def list_customers(db: Session = Depends(get_db)) -> list[Customer]:
    statement = select(Customer).order_by(Customer.customer_external_id.asc())
    return list(db.scalars(statement).all())


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer(customer_id: str, db: Session = Depends(get_db)) -> Customer:
    customer = (
        db.query(Customer)
        .filter(Customer.customer_external_id == customer_id)
        .one_or_none()
    )
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found.",
        )

    return customer
