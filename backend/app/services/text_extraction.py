from pathlib import Path

import pandas as pd
from pypdf import PdfReader

from app.models import Document


class TextExtractionError(Exception):
    pass


def extract_text_from_document(document: Document) -> str:
    if not document.source_path:
        raise TextExtractionError("Document has no source file path.")

    source_path = Path(document.source_path)
    if not source_path.exists():
        raise TextExtractionError("Document source file was not found.")

    if document.document_type == "pdf":
        return _extract_pdf_text(source_path)

    if document.document_type == "csv":
        return _extract_csv_text(source_path)

    raise TextExtractionError("Unsupported document type for processing.")


def _extract_pdf_text(source_path: Path) -> str:
    try:
        reader = PdfReader(str(source_path))
        page_texts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text and page_text.strip():
                page_texts.append(page_text.strip())
    except Exception as exc:
        raise TextExtractionError("Could not extract text from PDF.") from exc

    text = "\n\n".join(page_texts).strip()
    if not text:
        raise TextExtractionError("No readable text was found in the PDF.")

    return text


def _extract_csv_text(source_path: Path) -> str:
    try:
        dataframe = pd.read_csv(source_path)
    except Exception as exc:
        raise TextExtractionError("Could not read CSV file.") from exc

    if dataframe.empty and len(dataframe.columns) == 0:
        raise TextExtractionError("The CSV file is empty.")

    columns = ", ".join(str(column) for column in dataframe.columns)
    rows_as_csv = dataframe.to_csv(index=False)
    return f"CSV columns: {columns}\n\n{rows_as_csv}".strip()
