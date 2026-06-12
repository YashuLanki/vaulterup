"""
main.py
-------
Vaulterup AI Property Intelligence System
------------------------------------------
Single entry point for the entire system.

Usage:
    python main.py ingest        # Start the PDF watcher (Stage 1)
    python main.py stats         # Show database statistics
    python main.py query <text>  # Search the document database
"""

import sys
import logging
from pathlib import Path

from config import LOG_DIR

# ─── Logging Setup ────────────────────────────────────────────────────────────
# ASCII-only messages to avoid Windows cp1252 encoding errors.

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "vaulterup.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

log = logging.getLogger("vaulterup")


# ─── Commands ─────────────────────────────────────────────────────────────────

def cmd_ingest():
    """Start Stage 1 — PDF ingestion pipeline and folder watcher."""
    from ingestion.watcher import start_watcher

    log.info("=" * 60)
    log.info("  Vaulterup AI Property Intelligence System")
    log.info("  Stage 1 - PDF Ingestion Pipeline")
    log.info(f"  Watching : {Path('data/watched_folder').resolve()}")
    log.info(f"  Database : {Path('data/chroma_db').resolve()}")
    log.info(f"  OCR      : Tesseract (auto-activated for scanned PDFs)")
    log.info("=" * 60)

    start_watcher()


def cmd_stats():
    """Show a summary of everything stored in ChromaDB."""
    from ingestion.embedder import get_stats
    from ingestion.registry import load_registry

    stats    = get_stats()
    registry = load_registry()

    print(f"\n{'=' * 55}")
    print(f"  Vaulterup — Database Stats")
    print(f"{'=' * 55}")
    print(f"  Total chunks stored : {stats['total_chunks']}")
    print(f"  Documents ingested  : {len(registry)}")
    for _, info in registry.items():
        ocr_tag = " [OCR]" if info.get("ocr_used") else ""
        print(f"    * {info['filename']}{ocr_tag}")
        print(f"      {info['chunks']} chunks | {info['pages']} pages | ingested {info['ingested_at'][:10]}")
    print(f"{'=' * 55}\n")


def cmd_query(question: str):
    """Search ChromaDB for chunks relevant to a question."""
    from ingestion.embedder import query_documents

    results = query_documents(question, n_results=5)

    print(f"\nTop results for: '{question}'\n")
    if not results:
        print("No results found — database may be empty.")
        return

    for r in results:
        print(f"[{r['filename']} | chunk {r['chunk']} | score {r['score']} | ocr={r['ocr']}]")
        print(r["text"][:300])
        print("-" * 50)


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or args[0] == "ingest":
        cmd_ingest()

    elif args[0] == "stats":
        cmd_stats()

    elif args[0] == "query":
        if len(args) < 2:
            print("Usage: python main.py query <your question here>")
        else:
            cmd_query(" ".join(args[1:]))

    else:
        print("Usage:")
        print("  python main.py ingest        — start the PDF watcher")
        print("  python main.py stats         — show database stats")
        print("  python main.py query <text>  — search documents")
