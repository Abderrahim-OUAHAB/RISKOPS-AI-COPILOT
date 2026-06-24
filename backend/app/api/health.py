from pathlib import Path

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db

router = APIRouter()


@router.get("/health")
def health_check(db: Session = Depends(get_db)) -> dict:
    database_status = "ok"
    vector_extension_status = "unknown"
    model_status = "present" if Path(settings.churn_model_path).exists() else "missing"

    try:
        db.execute(text("SELECT 1"))
        vector_extension_status = "available" if vector_extension_available(db) else "missing"
    except Exception:
        database_status = "unavailable"

    api_status = "ok" if database_status == "ok" else "degraded"
    return {
        "status": api_status,
        "api": {"status": api_status},
        "database": {"status": database_status},
        "model": {"status": model_status, "path": settings.churn_model_path},
        "vector_extension": {"status": vector_extension_status},
        "airflow": {"hint": "Airflow UI is expected at http://localhost:8080 in local Docker."},
        "service": "riskops-api",
        "version": "0.1.0",
    }


@router.get("/ready")
def readiness_check(db: Session = Depends(get_db)) -> JSONResponse:
    checks = {
        "database": False,
        "tables": False,
        "model": Path(settings.churn_model_path).exists(),
        "monitoring_dir": False,
    }
    errors: list[str] = []

    try:
        db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as exc:
        errors.append(f"Database unavailable: {exc}")

    if checks["database"]:
        try:
            inspector = inspect(db.bind)
            existing_tables = set(inspector.get_table_names())
            required_tables = {"customers", "documents", "document_chunks", "risk_predictions"}
            missing_tables = sorted(required_tables.difference(existing_tables))
            checks["tables"] = not missing_tables
            if missing_tables:
                errors.append("Missing tables: " + ", ".join(missing_tables))
        except Exception as exc:
            errors.append(f"Could not inspect tables: {exc}")

    try:
        monitoring_dir = Path(settings.ml_monitoring_report_path).parent
        monitoring_dir.mkdir(parents=True, exist_ok=True)
        trace_dir = Path(settings.llm_traces_path).parent
        trace_dir.mkdir(parents=True, exist_ok=True)
        checks["monitoring_dir"] = monitoring_dir.exists() and trace_dir.exists()
    except Exception as exc:
        errors.append(f"Monitoring directory unavailable: {exc}")

    if not checks["model"]:
        errors.append(f"Churn model missing: {settings.churn_model_path}")

    ready = all(checks.values())
    return JSONResponse(
        status_code=status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"ready": ready, "checks": checks, "errors": errors},
    )


def vector_extension_available(db: Session) -> bool:
    result = db.execute(
        text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')")
    )
    return bool(result.scalar())
