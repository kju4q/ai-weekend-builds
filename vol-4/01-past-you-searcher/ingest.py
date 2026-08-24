"""Ingest your writing into a local searchable index.

    python3 ingest.py sample-data        # index the shipped synthetic sample
    python3 ingest.py my-writing         # index your own folder
    python3 ingest.py                    # defaults to my-writing/

Supported files: .md, .txt, and .json conversation exports in the one format
documented in the README. Hidden files (leading dot) and every other extension
are skipped and reported, not treated as an error.

Everything is written to index.json next to this script. Nothing is uploaded.

Re-running is safe: files are tracked by SHA-256, so only changed files are
re-embedded, deleted files are pruned, and the write is atomic.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import sys

from embeddings import backend_name, embed

HERE = pathlib.Path(__file__).parent
INDEX_PATH = HERE / "index.json"
DEFAULT_SOURCE_DIR = HERE / "my-writing"

SUPPORTED = {".md", ".txt", ".json"}

CHUNK_CHARS = 700
CHUNK_OVERLAP = 150

# date: 2024-01-20  or  Date: 2024/01/20  in the first few lines of a file
_META_DATE = re.compile(r"^\s*date\s*[:=]\s*(\d{4})[-/](\d{2})[-/](\d{2})", re.I | re.M)
# a 2024-01-20 prefix anywhere in the filename
_NAME_DATE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def file_hash(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_conversation(raw: str, name: str) -> tuple[str, str | None]:
    """Read the one supported JSON conversation format.

    {"title": "...", "date": "YYYY-MM-DD", "messages": [{"role": "...", "text": "..."}]}

    Returns (flattened text, date or None). Raises ValueError with a readable
    message when the shape is not what we support.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"not valid JSON ({e.msg} at line {e.lineno})") from None
    if not isinstance(data, dict):
        raise ValueError("top level must be a JSON object, see the README format")
    messages = data.get("messages")
    if not isinstance(messages, list) or not messages:
        raise ValueError('missing a non-empty "messages" list')

    parts = []
    title = data.get("title")
    if isinstance(title, str) and title.strip():
        parts.append(f"Conversation: {title.strip()}")
    for i, m in enumerate(messages):
        if not isinstance(m, dict):
            raise ValueError(f"message {i} is not an object")
        text = m.get("text")
        if not isinstance(text, str):
            raise ValueError(f'message {i} has no "text" string')
        role = m.get("role", "unknown")
        parts.append(f"{role}: {text.strip()}")

    date = data.get("date")
    if not (isinstance(date, str) and _NAME_DATE.fullmatch(date.strip())):
        date = None
    return "\n\n".join(parts), date


def extract_date(path: pathlib.Path, text: str, json_date: str | None) -> tuple[str, str]:
    """Return (YYYY-MM-DD, how it was found).

    Order, documented in the README and never guessed at:
      1. a metadata date in the file (a `date:` line, or "date" in a conversation)
      2. a YYYY-MM-DD prefix in the filename
      3. the file modification time
    """
    if json_date:
        return json_date.strip(), "metadata"
    m = _META_DATE.search("\n".join(text.splitlines()[:10]))
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}", "metadata"
    m = _NAME_DATE.search(path.name)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}", "filename"
    mtime = dt.datetime.fromtimestamp(path.stat().st_mtime)
    return mtime.strftime("%Y-%m-%d"), "file mtime"


def chunk(text: str) -> list[str]:
    text = " ".join(text.split())
    if not text:
        return []
    pieces = []
    start = 0
    step = max(1, CHUNK_CHARS - CHUNK_OVERLAP)
    while start < len(text):
        pieces.append(text[start : start + CHUNK_CHARS])
        start += step
    return [p for p in pieces if p.strip()]


def load_index() -> dict:
    if INDEX_PATH.exists():
        try:
            data = json.loads(INDEX_PATH.read_text())
            if data.get("backend") == backend_name():
                return data
            print("  ! embedding backend changed since the last run, rebuilding index")
        except (json.JSONDecodeError, OSError):
            print("  ! index.json was unreadable, rebuilding from scratch")
    return {"backend": backend_name(), "source_dir": None, "files": {}, "records": []}


def atomic_write(path: pathlib.Path, data: dict) -> None:
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data))
    os.replace(tmp, path)


def collect(source_dir: pathlib.Path) -> tuple[list[pathlib.Path], list[str]]:
    files, skipped = [], []
    for p in sorted(source_dir.rglob("*")):
        if not p.is_file():
            continue
        if any(part.startswith(".") for part in p.relative_to(source_dir).parts):
            skipped.append(f"{p.name} (hidden)")
            continue
        if p.suffix.lower() not in SUPPORTED:
            skipped.append(f"{p.name} ({p.suffix or 'no extension'} not supported)")
            continue
        files.append(p)
    return files, skipped


def main() -> None:
    source_dir = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SOURCE_DIR
    if not source_dir.is_absolute():
        source_dir = (pathlib.Path.cwd() / source_dir).resolve()

    if not source_dir.exists():
        print(f"No such folder: {source_dir}")
        print("Try:  python3 ingest.py sample-data")
        print("Or make a folder for your own writing:  mkdir my-writing")
        sys.exit(1)
    if not source_dir.is_dir():
        print(f"Not a folder: {source_dir}")
        sys.exit(1)

    files, skipped = collect(source_dir)
    for note in skipped:
        print(f"  skipped: {note}")
    if not files:
        print(f"\nNo .md, .txt, or .json files found in {source_dir}.")
        print("Add some writing and rerun. Supported: .md, .txt, .json (see README).")
        sys.exit(1)

    index = load_index()
    if index.get("source_dir") not in (None, str(source_dir)):
        print(f"  ! index was built from {index['source_dir']}, rebuilding for {source_dir}")
        index = {"backend": backend_name(), "source_dir": None, "files": {}, "records": []}

    known: dict[str, str] = index.get("files", {})
    disk = {str(p.relative_to(source_dir)): file_hash(p) for p in files}
    rel_of = {str(p.relative_to(source_dir)): p for p in files}

    changed = [rel for rel in disk if disk[rel] != known.get(rel)]
    deleted = [rel for rel in known if rel not in disk]
    unchanged = [rel for rel in disk if rel not in changed]

    if not changed and not deleted:
        print(f"\nNothing changed. Index has {len(index['records'])} chunks from "
              f"{len(disk)} files.\nIndex: {INDEX_PATH}")
        print('Ask it something:  python3 ask.py "what did I keep saying about building products?"')
        return

    stale = set(changed) | set(deleted)
    kept = [r for r in index.get("records", []) if r["source"] not in stale]

    for rel in deleted:
        print(f"  removed: {rel}")
    for rel in sorted(unchanged):
        print(f"  unchanged: {rel}")

    new_records: list[dict] = []
    failed: list[str] = []
    for rel in sorted(changed):
        path = rel_of[rel]
        raw = path.read_text(encoding="utf-8", errors="ignore")
        json_date = None
        if path.suffix.lower() == ".json":
            try:
                text, json_date = parse_conversation(raw, path.name)
            except ValueError as e:
                print(f"  ! skipped {rel}: {e}")
                failed.append(rel)
                continue
        else:
            text = raw
        if not text.strip():
            print(f"  ! skipped {rel}: file is empty")
            failed.append(rel)
            continue

        date, date_source = extract_date(path, raw, json_date)
        pieces = chunk(text)
        print(f"  indexed: {rel} -> {len(pieces)} chunks, date {date} (from {date_source})")
        for i, piece in enumerate(pieces):
            new_records.append({
                "source": rel,
                "chunk": i,
                "date": date,
                "date_source": date_source,
                "text": piece,
            })

    if new_records:
        print(f"\nEmbedding {len(new_records)} chunks with backend: {backend_name()} ...")
        vectors = embed([r["text"] for r in new_records])
        for r, v in zip(new_records, vectors):
            r["vector"] = v

    records = kept + new_records
    if not records:
        print("\nNothing could be indexed. Every candidate file failed to read.")
        sys.exit(1)

    files_map = {rel: h for rel, h in known.items() if rel not in stale}
    for rel in changed:
        if rel not in failed:
            files_map[rel] = disk[rel]

    atomic_write(INDEX_PATH, {
        "backend": backend_name(),
        "source_dir": str(source_dir),
        "files": files_map,
        "records": records,
    })

    print(f"\nFiles read:    {len(files_map)}")
    print(f"Chunks:        {len(records)}")
    print(f"Backend:       {backend_name()}")
    print(f"Index:         {INDEX_PATH}")
    print('\nAsk it something:  python3 ask.py "what did I keep saying about building products?"')


if __name__ == "__main__":
    main()
