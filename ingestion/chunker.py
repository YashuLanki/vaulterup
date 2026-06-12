"""
ingestion/chunker.py
--------------------
Splits extracted PDF text into overlapping chunks for storage in ChromaDB.

Why chunking matters:
  - Claude can only search and retrieve focused pieces of text, not entire documents
  - Overlapping chunks preserve context across boundaries
  - Smaller chunks = more precise search results
"""

from config import CHUNK_SIZE, CHUNK_OVERLAP


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Split text into overlapping chunks.

    Strategy:
      1. First tries to split on paragraph boundaries (double newlines)
      2. For paragraphs longer than chunk_size, falls back to character splitting
      3. Each new chunk starts with the last `overlap` characters of the previous chunk
         to preserve context across boundaries

    Args:
        text:       The full extracted text from a PDF
        chunk_size: Maximum characters per chunk (default from config)
        overlap:    Characters to carry over between chunks (default from config)

    Returns:
        List of non-empty text chunks
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        # Paragraph is too long on its own — hard split it
        if len(para) > chunk_size:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            for i in range(0, len(para), chunk_size - overlap):
                chunks.append(para[i : i + chunk_size].strip())

        # Paragraph fits in the current chunk
        elif len(current_chunk) + len(para) + 2 <= chunk_size:
            current_chunk += ("\n\n" if current_chunk else "") + para

        # Paragraph doesn't fit — flush current chunk and start a new one
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
            current_chunk = overlap_text + "\n\n" + para

    # Don't forget the last chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return [c for c in chunks if c]
