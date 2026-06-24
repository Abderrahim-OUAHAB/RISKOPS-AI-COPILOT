from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
sys.path.append(str(BACKEND_ROOT))
sys.path.append(str(PROJECT_ROOT))

from app.db.session import SessionLocal  # noqa: E402
from app.services.ml_monitoring_service import generate_ml_monitoring_report  # noqa: E402


def main() -> None:
    db = SessionLocal()
    try:
        result = generate_ml_monitoring_report(db)
        print(result)
    finally:
        db.close()


if __name__ == "__main__":
    main()
