"""
ingestion/watcher.py
--------------------
Monitors the watched_folder for new PDF files and triggers the ingestion
pipeline automatically when a new file is detected.

Uses the watchdog library to listen for file system events in real time.
"""

import logging
import shutil
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from config import WATCH_DIR, PROCESSED_DIR
from ingestion.extractor import extract
from ingestion.chunker import chunk_text
from ingestion.embedder import store_chunks
from ingestion.registry import (
    get_file_hash,
    is_already_ingested,
    record_ingestion,
)

log = logging.getLogger("vaulterup.watcher")


# ─── Core Ingestion Function ──────────────────────────────────────────────────

def ingest_pdf(path: Path):
    """
    Full ingestion pipeline for a single PDF file:
      1. Hash the file to check for duplicates
      2. Extract text (pdfplumber or OCR)
      3. Split into chunks
      4. Store chunks in ChromaDB
      5. Move file to processed/
      6. Record in registry
    """
    log.info(f"[INGEST] {path.name}")

    doc_hash = get_file_hash(path)

    if is_already_ingested(doc_hash):
        log.info(f"  [SKIP] Already ingested: {path.name}")
        return

    try:
        # Step 1: Extract text
        log.info("  Extracting text...")
        text, metadata = extract(path)

        if not text.strip():
            log.warning(f"  [WARN] No text extracted from {path.name} even after OCR")
            return

        method = "OCR" if metadata["ocr_used"] else "direct"
        log.info(f"  Extracted {len(text):,} characters via {method} from {metadata['page_count']} pages")

        # Step 2: Chunk
        chunks = chunk_text(text)
        log.info(f"  Split into {len(chunks)} chunks")

        # Step 3: Store in ChromaDB
        store_chunks(chunks, metadata, doc_hash)

        # Step 4: Move to processed/
        dest = PROCESSED_DIR / path.name
        shutil.move(str(path), str(dest))
        log.info("  Moved to processed/")

        # Step 5: Record in registry
        record_ingestion(
            file_hash=doc_hash,
            filename=path.name,
            chunks=len(chunks),
            pages=metadata["page_count"],
            ocr_used=metadata["ocr_used"],
        )

        log.info(f"  [DONE] {path.name} ({len(chunks)} chunks, method={method})\n")

    except Exception as e:
        log.error(f"  [ERROR] Failed to ingest {path.name}: {e}", exc_info=True)


# ─── Watchdog Event Handler ───────────────────────────────────────────────────

class PDFHandler(FileSystemEventHandler):
    """Triggers ingestion when a new PDF file appears in the watched folder."""

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() == ".pdf":
            time.sleep(1)  # Small delay to ensure file is fully written
            ingest_pdf(path)

    def on_moved(self, event):
        """Also catches files moved or copied into the folder."""
        if event.is_directory:
            return
        path = Path(event.dest_path)
        if path.suffix.lower() == ".pdf":
            time.sleep(1)
            ingest_pdf(path)


# ─── Startup Processing ───────────────────────────────────────────────────────

def process_existing_pdfs():
    """On startup, ingest any PDFs already sitting in the watched folder."""
    existing = list(WATCH_DIR.glob("*.pdf"))
    if existing:
        log.info(f"Found {len(existing)} existing PDF(s) — ingesting now...")
        for pdf_path in existing:
            ingest_pdf(pdf_path)
    else:
        log.info("Watched folder is empty — waiting for new PDFs...")


# ─── Watcher Entry Point ──────────────────────────────────────────────────────

def start_watcher():
    """Start the folder watcher. Runs until manually stopped (Ctrl+C)."""
    process_existing_pdfs()

    observer = Observer()
    observer.schedule(PDFHandler(), str(WATCH_DIR), recursive=False)
    observer.start()
    log.info("[ACTIVE] Watcher running — drop PDFs into data/watched_folder to ingest them\n")

    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        log.info("Shutting down watcher...")
        observer.stop()
    observer.join()
