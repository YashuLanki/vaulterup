# Vaulterup AI Property Intelligence System

An end-to-end AI system built for a real estate investment company to automate
market intelligence, document analysis, and meeting knowledge capture.

Built as a data analyst intern project using Python, Claude AI, and a modern
RAG (Retrieval-Augmented Generation) architecture.

---

## System Overview

| Stage | Name | Description | Status |
|-------|------|-------------|--------|
| 1 | PDF Ingestion | Watches a folder, extracts text from PDFs (including scanned documents via OCR), and stores chunks in a vector database | Complete |
| 2 | Web & Email Pipeline | Scrapes public market data and reads broker emails automatically | In Progress |
| 3 | Claude Analysis Layer | RAG system that generates market summaries, risk flags, and answers questions using ingested documents | Planned |
| 4 | Live Dashboard | Streamlit dashboard displaying all AI insights for the whole team | Planned |
| 5 | Speech-to-Knowledge | Records Monday meetings, transcribes audio, and extracts structured property updates | Planned |

---

## Tech Stack

- **PDF Extraction** — pdfplumber, Tesseract OCR, pdf2image
- **Vector Database** — ChromaDB
- **AI Analysis** — Anthropic Claude API
- **Web Scraping** — BeautifulSoup, Requests
- **Email Integration** — Gmail API
- **Dashboard** — Streamlit
- **Transcription** — OpenAI Whisper

---

## Project Structure

```
vaulterup/
  main.py               # Entry point — runs all stages
  config.py             # All settings and paths in one place
  requirements.txt      # All dependencies
  README.md             # This file

  ingestion/            # Stage 1: PDF Ingestion
    extractor.py        # PDF text extraction + OCR fallback
    chunker.py          # Splits text into overlapping chunks
    embedder.py         # ChromaDB vector storage and retrieval
    watcher.py          # Folder monitoring and ingestion pipeline
    registry.py         # Duplicate detection via file hashing

  pipeline/             # Stage 2: Web & Email Data Pipeline
    scraper.py          # Public web data scraping
    email_reader.py     # Gmail/Outlook broker email reader

  analysis/             # Stage 3: Claude RAG Analysis Layer
    rag.py              # Claude-powered document Q&A and insights

  dashboard/            # Stage 4: Live Dashboard
    app.py              # Streamlit dashboard

  speech/               # Stage 5: Speech-to-Knowledge Pipeline
    transcriber.py      # Whisper audio transcription
    extractor.py        # Claude meeting data extraction
    review.py           # Human review screen

  data/
    watched_folder/     # Drop PDFs here to ingest them
    processed/          # PDFs move here after ingestion
    chroma_db/          # Vector database storage
    logs/               # Ingestion and system logs
```

---

## Setup

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/vaulterup.git
cd vaulterup
```

### 2. Create a virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate  # Mac/Linux
```

### 3. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 4. Install external tools (Windows)
- **Tesseract OCR**: https://github.com/UB-Mannheim/tesseract/wiki
- **Poppler**: https://github.com/oschwartz10612/poppler-windows/releases

### 5. Update paths in config.py
```python
TESSERACT_PATH = r"C:\path\to\Tesseract-OCR\tesseract.exe"
POPPLER_PATH   = r"C:\path\to\poppler\Library\bin"
```

### 6. Create data folders
```bash
mkdir data\watched_folder data\processed data\chroma_db data\logs
```

---

## Usage

```bash
# Start the PDF watcher (Stage 1)
python main.py ingest

# Show database statistics
python main.py stats

# Search ingested documents
python main.py query "flood zone designation Magic Ranch"
python main.py query "easement pipeline"
python main.py query "legal description parcel"
```

---

## How It Works

1. Drop any PDF into `data/watched_folder/`
2. The system detects it automatically
3. Text is extracted (or OCR runs for scanned documents)
4. Text is split into overlapping chunks and stored in ChromaDB
5. Claude can now search and answer questions about the document

Duplicate files are automatically detected using SHA-256 hashing —
the same document can be dropped multiple times without creating duplicate entries.

---

*Built by Yashu Lanki — Data Analyst Intern, Vaulterup*
