"""
ingestion/extractor.py
----------------------
Handles all PDF text extraction for the Vaulterup ingestion pipeline.

Two strategies are used automatically:
  1. pdfplumber  — fast, for text-based PDFs (market reports, broker packages)
  2. Tesseract   — OCR fallback for scanned/image PDFs (surveys, drawings)
"""

import logging
from datetime import datetime
from pathlib import Path

import pdfplumber
import pytesseract
from pdf2image import convert_from_path

from config import TESSERACT_PATH, POPPLER_PATH

# Point pytesseract to the correct Tesseract executable on Windows
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

log = logging.getLogger("vaulterup.extractor")


def extract(path: Path) -> tuple[str, dict]:
    """
    Main extraction entry point.
    Tries pdfplumber first, falls back to OCR if no text is found.
    Returns (full_text, metadata_dict).
    """
    metadata = {
        "filename":    path.name,
        "ingested_at": datetime.now().isoformat(),
        "page_count":  0,
        "has_tables":  False,
        "ocr_used":    False,
    }

    # --- Strategy 1: pdfplumber (text-based PDFs) ---
    text, metadata = _extract_with_pdfplumber(path, metadata)

    # --- Strategy 2: OCR fallback (scanned/image PDFs) ---
    if not text.strip():
        log.info("  No text layer found — running OCR (this may take a moment)...")
        text = _extract_with_ocr(path, metadata)
        metadata["ocr_used"] = True

    return text, metadata


def _extract_with_pdfplumber(path: Path, metadata: dict) -> tuple[str, dict]:
    """Extract text and tables from a text-based PDF using pdfplumber."""
    full_text = []

    with pdfplumber.open(path) as pdf:
        metadata["page_count"] = len(pdf.pages)

        if pdf.metadata:
            metadata["pdf_title"]  = pdf.metadata.get("Title", "") or ""
            metadata["pdf_author"] = pdf.metadata.get("Author", "") or ""

        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text:
                full_text.append(f"[Page {page_num}]\n{text.strip()}")

            tables = page.extract_tables()
            if tables:
                metadata["has_tables"] = True
                for table in tables:
                    table_text = _table_to_text(table, page_num)
                    if table_text:
                        full_text.append(table_text)

    return "\n\n".join(full_text), metadata


def _extract_with_ocr(path: Path, metadata: dict) -> str:
    """
    Convert each PDF page to an image and run Tesseract OCR.
    Used automatically for scanned or image-based PDFs.
    """
    pages = convert_from_path(str(path), dpi=300, poppler_path=POPPLER_PATH)
    metadata["page_count"] = len(pages)

    ocr_text = []
    for i, page_image in enumerate(pages, start=1):
        log.info(f"  OCR processing page {i}/{len(pages)}...")
        text = pytesseract.image_to_string(page_image, lang="eng")
        if text.strip():
            ocr_text.append(f"[Page {i} - OCR]\n{text.strip()}")

    return "\n\n".join(ocr_text)


def _table_to_text(table: list, page_num: int) -> str:
    """Convert a pdfplumber table (list of lists) into readable plain text."""
    if not table:
        return ""
    lines = [f"[Table on Page {page_num}]"]
    for row in table:
        cleaned = [str(cell).strip() if cell else "" for cell in row]
        lines.append(" | ".join(cleaned))
    return "\n".join(lines)
