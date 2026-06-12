"""
ingestion/registry.py
---------------------
Tracks which PDFs have already been ingested using SHA-256 file hashing.
Prevents duplicate documents from being stored in ChromaDB.
"""

import hashlib
import json
from pathlib import Path

from config import REGISTRY_FILE


def load_registry() -> dict:
    """Load the ingestion registry from disk. Returns empty dict if none exists."""
    if REGISTRY_FILE.exists():
        with open(REGISTRY_FILE) as f:
            return json.load(f)
    return {}


def save_registry(registry: dict):
    """Save the ingestion registry to disk."""
    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry, f, indent=2)


def get_file_hash(path: Path) -> str:
    """
    Compute a SHA-256 hash of a file's contents.
    Used to detect duplicate files regardless of filename.
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def is_already_ingested(file_hash: str) -> bool:
    """Return True if this file hash exists in the registry."""
    registry = load_registry()
    return file_hash in registry


def record_ingestion(file_hash: str, filename: str, chunks: int, pages: int, ocr_used: bool):
    """Add a successfully ingested file to the registry."""
    from datetime import datetime
    registry = load_registry()
    registry[file_hash] = {
        "filename":    filename,
        "ingested_at": datetime.now().isoformat(),
        "chunks":      chunks,
        "pages":       pages,
        "ocr_used":    ocr_used,
    }
    save_registry(registry)
