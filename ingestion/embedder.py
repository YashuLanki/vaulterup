"""
ingestion/embedder.py
---------------------
Handles all ChromaDB interactions for the Vaulterup ingestion pipeline.

Responsibilities:
  - Initializing the ChromaDB client and collection
  - Converting text chunks into vector embeddings
  - Storing and retrieving chunks with metadata
  - Reporting collection statistics

Embedding note:
  Currently uses LocalHashEmbedding — a lightweight deterministic embedding
  that requires no model downloads. For production, swap to sentence-transformers
  or the Anthropic Embeddings API for true semantic search quality.
"""

import hashlib
import logging

import numpy as np
import chromadb
from chromadb import EmbeddingFunction, Documents, Embeddings

from config import CHROMA_DIR, CHROMA_COLLECTION_NAME, EMBEDDING_DIM

log = logging.getLogger("vaulterup.embedder")


# ─── Embedding Function ───────────────────────────────────────────────────────

class LocalHashEmbedding(EmbeddingFunction):
    """
    Deterministic pseudo-embedding based on word position hashing.
    No model downloads required — safe for offline environments.

    Production upgrade path:
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
        ef = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    """

    def __init__(self):
        pass

    def __call__(self, input: Documents) -> Embeddings:
        result = []
        for text in input:
            words = text.lower().split()
            vec = np.zeros(EMBEDDING_DIM)
            for i, word in enumerate(words[:500]):
                h = int(hashlib.md5(word.encode()).hexdigest(), 16)
                idx = h % EMBEDDING_DIM
                vec[idx] += 1.0 / (i + 1)
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            result.append(vec.tolist())
        return result


# ─── ChromaDB Client ──────────────────────────────────────────────────────────

def get_collection():
    """Initialize and return the ChromaDB collection."""
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        embedding_function=LocalHashEmbedding(),
        metadata={"hnsw:space": "cosine"},
    )
    return collection


# ─── Storage ──────────────────────────────────────────────────────────────────

def store_chunks(chunks: list[str], metadata: dict, doc_hash: str):
    """
    Store text chunks in ChromaDB with associated metadata.
    Each chunk gets a unique ID based on document hash + chunk index.
    """
    if not chunks:
        log.warning(f"No chunks to store for {metadata['filename']}")
        return

    collection = get_collection()

    ids = [f"{doc_hash}_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "filename":     metadata["filename"],
            "ingested_at":  metadata["ingested_at"],
            "page_count":   str(metadata["page_count"]),
            "has_tables":   str(metadata["has_tables"]),
            "ocr_used":     str(metadata["ocr_used"]),
            "chunk_index":  str(i),
            "total_chunks": str(len(chunks)),
            "doc_hash":     doc_hash,
        }
        for i in range(len(chunks))
    ]

    collection.add(documents=chunks, metadatas=metadatas, ids=ids)
    log.info(f"  Stored {len(chunks)} chunks in ChromaDB")


# ─── Retrieval ────────────────────────────────────────────────────────────────

def query_documents(question: str, n_results: int = 5) -> list[dict]:
    """
    Search ChromaDB for chunks relevant to a question.
    Returns a ranked list of results with text, source, and relevance score.
    """
    collection = get_collection()
    count = collection.count()

    if count == 0:
        return []

    results = collection.query(
        query_texts=[question],
        n_results=min(n_results, count),
    )

    output = []
    if results and results["documents"]:
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i]
            dist = results["distances"][0][i] if results.get("distances") else None
            output.append({
                "text":     doc,
                "filename": meta.get("filename"),
                "chunk":    meta.get("chunk_index"),
                "ocr":      meta.get("ocr_used"),
                "score":    round(1 - dist, 4) if dist is not None else None,
            })
    return output


def get_stats() -> dict:
    """Return a summary of what is currently stored in ChromaDB."""
    collection = get_collection()
    return {"total_chunks": collection.count()}
