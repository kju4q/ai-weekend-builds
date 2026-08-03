"""Ingest: docs/ -> chunks -> embeddings -> local vector store (index.json).

Run this whenever you add or change documents:

    python ingest.py

Supported files in docs/: .txt, .md, and .pdf (PDF needs `pip install pypdf`).
Everything stays on disk in index.json. Nothing is uploaded anywhere.

Incremental: only files whose content has changed (detected via SHA-256) are
re-embedded. Deleted files are pruned from the index automatically.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys

from embeddings import embed, backend_name

DOCS_DIR = pathlib.Path(__file__).parent / "docs"
INDEX_PATH = pathlib.Path(__file__).parent / "index.json"

CHUNK_CHARS = 800
CHUNK_OVERLAP = 150


def file_hash(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def load_index() -> dict:
    if INDEX_PATH.exists():
        try:
            data = json.loads(INDEX_PATH.read_text())
            # Vectors from a different backend are not comparable, so rebuild.
            if data.get("backend") == backend_name():
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return {"backend": backend_name(), "files": {}, "records": []}


def atomic_write(path: pathlib.Path, data: dict) -> None:
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data))
    os.replace(tmp, path)  # atomic on POSIX and Windows


def main() -> None:
    if not DOCS_DIR.exists():
        DOCS_DIR.mkdir(parents=True)
    files = [p for p in sorted(DOCS_DIR.iterdir())
             if p.suffix.lower() in {".txt", ".md", ".pdf"}]
    if not files:
        print(f"No documents in {DOCS_DIR}. Drop some .txt / .md / .pdf files in and rerun.")
        sys.exit(1)

    index = load_index()
    known_hashes: dict[str, str] = index.get("files", {})

    # Scan disk hashes once
    disk_hashes = {p.name: file_hash(p) for p in files}

    changed = [p for p in files if disk_hashes[p.name] != known_hashes.get(p.name)]
    deleted = [name for name in known_hashes if name not in disk_hashes]
    unchanged = [p for p in files if p.name not in {c.name for c in changed}]

    if not changed and not deleted:
        print(f"Nothing changed. Index has {len(index['records'])} chunks. Run: python ask.py")
        return

    # Drop records for changed or deleted files
    stale = {p.name for p in changed} | set(deleted)
    kept_records = [r for r in index.get("records", []) if r["source"] not in stale]

    for name in deleted:
        print(f"  removed: {name}")
    for p in unchanged:
        print(f"  unchanged: {p.name} (skipped)")

    # Embed only changed files
    new_records: list[dict] = []
    for path in changed:
        text = read_file(path)
        if not text.strip():
            continue
        pieces = chunk(text)
        print(f"  {path.name}: {len(pieces)} chunks (re-embedding)")
        for i, piece in enumerate(pieces):
            new_records.append({"source": path.name, "chunk": i, "text": piece})

    if new_records:
        print(f"Embedding {len(new_records)} chunks with backend: {backend_name()} ...")
        vectors = embed([r["text"] for r in new_records])
        for r, v in zip(new_records, vectors):
            r["vector"] = v

    all_records = kept_records + new_records
    new_files = {**{n: h for n, h in known_hashes.items() if n not in stale},
                 **{p.name: disk_hashes[p.name] for p in changed}}

    atomic_write(INDEX_PATH, {
        "backend": backend_name(),
        "files": new_files,
        "records": all_records,
    })
    print(f"Wrote {INDEX_PATH.name} ({len(all_records)} chunks total). Now run: python ask.py")


if __name__ == "__main__":
    main()
