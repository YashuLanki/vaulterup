"""
config.py
---------
Central configuration for the Vaulterup AI Property Intelligence System.
All paths, settings, and constants live here.
To adapt this project to a new machine, only this file needs to be updated.
"""

from pathlib import Path

# ─── Project Root ─────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent

# ─── Data Folders ─────────────────────────────────────────────────────────────

DATA_DIR       = BASE_DIR / "data"
WATCH_DIR      = DATA_DIR / "watched_folder"
PROCESSED_DIR  = DATA_DIR / "processed"
CHROMA_DIR     = DATA_DIR / "chroma_db"
LOG_DIR        = DATA_DIR / "logs"
REGISTRY_FILE  = DATA_DIR / "ingested_registry.json"

# ─── Chunking Settings ────────────────────────────────────────────────────────

CHUNK_SIZE    = 800   # characters per chunk
CHUNK_OVERLAP = 100   # overlap between chunks to preserve context

# ─── OCR Settings (Windows paths) ─────────────────────────────────────────────
# Update these paths if Tesseract or Poppler are installed in a different location.

TESSERACT_PATH = r"C:\Users\YashuLanki\Packages\Tesseract-OCR\tesseract.exe"
POPPLER_PATH   = r"C:\Users\YashuLanki\Packages\poppler-26.02.0\Library\bin"

# ─── ChromaDB Settings ────────────────────────────────────────────────────────

CHROMA_COLLECTION_NAME = "vaulterup_documents"

# ─── Embedding Settings ───────────────────────────────────────────────────────
# Current: LocalHashEmbedding (no downloads required)
# Production upgrade: switch to "sentence_transformer" for better search quality

EMBEDDING_MODE = "local"  # options: "local", "sentence_transformer"
EMBEDDING_DIM  = 384
