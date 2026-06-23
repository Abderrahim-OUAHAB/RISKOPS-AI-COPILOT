import re
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


def sanitize_filename(filename: str) -> str:
    safe_name = Path(filename).name.strip()
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", safe_name)
    return safe_name or "upload"


def save_upload_file(upload_file: UploadFile, raw_data_dir: Path) -> tuple[Path, int]:
    raw_data_dir.mkdir(parents=True, exist_ok=True)

    safe_filename = sanitize_filename(upload_file.filename or "upload")
    destination = raw_data_dir / f"{uuid4().hex}_{safe_filename}"

    upload_file.file.seek(0)
    with destination.open("wb") as output_file:
        shutil.copyfileobj(upload_file.file, output_file)

    file_size = destination.stat().st_size
    if file_size == 0:
        destination.unlink(missing_ok=True)
        raise ValueError("Uploaded file is empty.")

    return destination, file_size
