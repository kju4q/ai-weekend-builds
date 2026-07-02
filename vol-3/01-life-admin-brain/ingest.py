"""Ingest: docs/ -> chunks -> embeddings -> local vector store (index.json).

Run this whenever you add or change documents:

    python ingest.py

Supported files in docs/: .txt, .md, and .pdf (PDF needs `pip install pypdf`).
Everything stays on disk in index.json. Nothing is uploaded anywhere.
"""

from __future__ import annotations

import json
import pathlib
import sys

from embeddings import embed, backend_name

DOCS_DIR = pathlib.Path(__file__).parent / "docs"
INDEX_PATH = pathlib.Path(__file__).parent / "index.json"

CHUNK_CHARS = 800
CHUNK_OVERLAP = 150


def read_pdf(path: pathlib.Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        print(f"  ! skipping {path.name}: run `pip install pypdf` to read PDFs")
        return ""
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def read_file(path: pathlib.Path) -> str:
    if path.suffix.lower() == ".pdf":
        return read_pdf(path)
    return path.read_text(encoding="utf-8", errors="ignore")


def chunk(text: str) -> list[str]:
    text = " ".join(text.split())  # collapse whitespace
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_CHARS
        chunks.append(text[start:end])
        start = end - CHUNK_OVERLAP
    return [c for c in chunks if c.strip()]


def main() -> None:
    if not DOCS_DIR.exists():
        DOCS_DIR.mkdir(parents=True)
    files = [p for p in sorted(DOCS_DIR.iterdir())
             if p.suffix.lower() in {".txt", ".md", ".pdf"}]
    if not files:
        print(f"No documents in {DOCS_DIR}. Drop some .txt / .md / .pdf files in and rerun.")
        sys.exit(1)

    records = []
    for path in files:
        text = read_file(path)
        if not text.strip():
            continue
        pieces = chunk(text)
        print(f"  {path.name}: {len(pieces)} chunks")
        for i, piece in enumerate(pieces):
            records.append({"source": path.name, "chunk": i, "text": piece})

    print(f"Embedding {len(records)} chunks with backend: {backend_name()} ...")
    vectors = embed([r["text"] for r in records])
    for r, v in zip(records, vectors):
        r["vector"] = v

    INDEX_PATH.write_text(json.dumps({"backend": backend_name(), "records": records}))
    print(f"Wrote {INDEX_PATH.name} ({len(records)} chunks). Now run: python ask.py")


if __name__ == "__main__":
    main()
