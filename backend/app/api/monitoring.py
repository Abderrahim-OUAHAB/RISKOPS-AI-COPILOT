from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.services.llm_observability_service import read_traces, summarize_traces
from app.services.ml_monitoring_service import (
    generate_ml_monitoring_report,
    get_ml_report_status,
)

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("/ml/report")
def ml_report_status(format: str = Query(default="json", pattern="^(json|html)$")):
    if format == "html":
        report_path = Path(settings.ml_monitoring_report_path)
        if not report_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ML monitoring report has not been generated yet.",
            )
        return FileResponse(report_path, media_type="text/html")

    return get_ml_report_status()


@router.post("/ml/generate-report")
def generate_ml_report(db: Session = Depends(get_db)) -> dict:
    return generate_ml_monitoring_report(db)


@router.get("/llm/traces")
def llm_traces(limit: int = Query(default=20, ge=1, le=200)) -> list[dict]:
    return read_traces(limit=limit)


@router.get("/llm/summary")
def llm_summary() -> dict:
    return summarize_traces()
