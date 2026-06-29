import re
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


def sanitize_filename(filename: str) -> str:
    safe_name = Path(filename).name.strip()
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", safe_name)
    return safe_name or "upload"


def save_upload_file(
    upload_file: UploadFile,
    raw_data_dir: Path,
    max_size_bytes: int | None = None,
) -> tuple[Path, int]:
    raw_data_dir.mkdir(parents=True, exist_ok=True)

    safe_filename = sanitize_filename(upload_file.filename or "upload")
    destination = raw_data_dir / f"{uuid4().hex}_{safe_filename}"

    file_size = 0
    upload_file.file.seek(0)
    with destination.open("wb") as output_file:
        while True:
            chunk = upload_file.file.read(1024 * 1024)
            if not chunk:
                break

            file_size += len(chunk)
            if max_size_bytes is not None and file_size > max_size_bytes:
                destination.unlink(missing_ok=True)
                max_size_mb = max_size_bytes // (1024 * 1024)
                raise ValueError(
                    f"Uploaded file is too large. Maximum allowed size is {max_size_mb} MB."
                )

            output_file.write(chunk)

    if file_size == 0:
        destination.unlink(missing_ok=True)
        raise ValueError("Uploaded file is empty.")

    return destination, file_size
