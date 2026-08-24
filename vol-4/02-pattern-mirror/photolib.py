"""Scanning, dates, duplicate detection, timeline maths, and local vision.

Everything in this module runs on your machine. Nothing here opens a network
connection except the one-time model download inside `classify()`, which pulls
the local CLIP weights from Hugging Face the first time you use `--vision local`.

Deliberately absent: face detection, face recognition, identity clustering,
people counting, and any "who was in this photo" analysis. This tool measures
when photos exist and what broad kind of scene they show. It does not look for
people, and the category list has no person-related label in it.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import pathlib
import re
from collections import Counter, defaultdict

from PIL import Image, ImageOps, UnidentifiedImageError

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp"}

EXIF_DATETIME_ORIGINAL = 0x9003
EXIF_DATETIME = 0x0132
EXIF_SUB_IFD = 0x8769

# YYYY-MM-DD or YYYY_MM_DD or YYYYMMDD in a filename
_NAME_DATE = re.compile(r"(20\d{2})[-_]?(0[1-9]|1[0-2])[-_]?(0[1-9]|[12]\d|3[01])")

# The fixed category list. Broad on purpose, and with no person, group, social,
# or identity label: this project does not classify people. Each category is a
# small ensemble of phrasings whose embeddings are averaged into one prototype,
# which is standard practice for zero-shot CLIP and measurably steadier than a
# single sentence. Changing this list changes the cache fingerprint, so stored
# labels are never reused against a different list.
CATEGORIES = {
    "nature": [
        "a photo of nature", "trees and plants outdoors",
        "an open natural landscape", "a park with grass and trees",
        "a beach and the sea", "the ocean and the sky",
        "water and a natural horizon",
    ],
    "city_or_streets": [
        "a photo of a city street", "buildings in a city",
        "an urban street scene", "a photo of a road and buildings",
    ],
    "travel_or_landmarks": [
        "a photo of a famous landmark", "a monument or tower",
        "a tourist landmark while travelling",
    ],
    "food": [
        "a photo of a meal", "food on a plate", "a photo of a drink",
        "a restaurant dish",
    ],
    "animals": [
        "a photo of an animal", "a pet dog or cat", "a photo of a bird",
    ],
    "work_or_screens": [
        "a photo of a desk and computer", "a computer screen on a desk",
        "a workspace with a monitor", "a laptop on a table",
    ],
    "documents_or_screenshots": [
        "a screenshot of a screen", "a page of text", "a scanned document",
        "a photo of printed paper",
    ],
    "art_or_objects": [
        "a still life of objects", "a photo of objects on a shelf",
        "a work of art", "a vase and small objects",
    ],
    "events_or_decorations": [
        "a party with decorations", "a celebration with balloons",
        "a decorated room for an event",
    ],
    "home_or_interior": [
        "the interior of a home", "a living room with furniture",
        "a photo of a room inside a house", "a window and furniture indoors",
    ],
}

# The indoor/outdoor axis is scored separately, as a straight two-way comparison.
# It describes the picture, not how the photographer spends their time. Because a
# two-way choice starts at 50% by chance, it carries its own higher threshold.
INDOOR_OUTDOOR = {
    "indoors": [
        "a photo taken indoors", "an indoor scene inside a building",
        "the inside of a room", "an interior photograph",
    ],
    "outdoors": [
        "a photo taken outdoors", "an outdoor scene under the open sky",
        "outside in the open air", "an exterior photograph taken outside",
    ],
}

MODEL_NAME = "clip-ViT-B-32"
CACHE_VERSION = 3


# ---------------------------------------------------------------- scanning

def file_hash(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def _exif_date(img: Image.Image) -> str | None:
    try:
        exif = img.getexif()
    except Exception:
        return None
    if not exif:
        return None
    raw = exif.get_ifd(EXIF_SUB_IFD).get(EXIF_DATETIME_ORIGINAL) or exif.get(EXIF_DATETIME)
    if not isinstance(raw, str):
        return None
    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return dt.datetime.strptime(raw.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _name_date(name: str) -> str | None:
    m = _NAME_DATE.search(name)
    if not m:
        return None
    try:
        return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
    except ValueError:
        return None


def dhash(img: Image.Image, size: int = 8) -> str:
    """A 64-bit difference hash. Near-identical pictures land within a few bits
    of each other, which is what burst photos and re-saves look like."""
    small = img.convert("L").resize((size + 1, size), Image.Resampling.LANCZOS)
    px = list(small.getdata())
    bits = 0
    for row in range(size):
        base = row * (size + 1)
        for col in range(size):
            bits = (bits << 1) | int(px[base + col] < px[base + col + 1])
    return f"{bits:016x}"


def hamming(a: str, b: str) -> int:
    return bin(int(a, 16) ^ int(b, 16)).count("1")


def scan(root: pathlib.Path, skip_dirs: set[pathlib.Path]) -> tuple[list[dict], list[str]]:
    """Walk the folder and return (accepted records, skip notes).

    One unreadable file is a skip note, never a crash.
    """
    records, skipped = [], []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part.startswith(".") for part in rel.parts):
            skipped.append(f"{rel} (hidden)")
            continue
        if any(_is_within(path, d) for d in skip_dirs):
            continue  # our own output folder, silently
        if path.suffix.lower() not in SUPPORTED:
            skipped.append(f"{rel} ({path.suffix.lower() or 'no extension'} not supported)")
            continue
        try:
            with Image.open(path) as img:
                img.load()
                oriented = ImageOps.exif_transpose(img)
                width, height = oriented.size
                date = _exif_date(img)
                date_source = "exif"
                phash = dhash(oriented)
        except (UnidentifiedImageError, OSError, ValueError) as e:
            skipped.append(f"{rel} (unreadable: {type(e).__name__})")
            continue

        if not date:
            date = _name_date(path.name)
            date_source = "filename" if date else date_source
        if not date:
            date = dt.date.fromtimestamp(path.stat().st_mtime).isoformat()
            date_source = "file mtime"

        records.append({
            "rel": str(rel),
            "name": path.name,
            "date": date,
            "date_source": date_source,
            "month": date[:7],
            "width": width,
            "height": height,
            "orientation": "portrait" if height > width else "landscape",
            "bytes": path.stat().st_size,
            "sha256": file_hash(path),
            "phash": phash,
        })
    return records, skipped


def _is_within(path: pathlib.Path, parent: pathlib.Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


# ---------------------------------------------------------------- duplicates

def mark_duplicates(records: list[dict], threshold: int) -> dict:
    """Group exact and near-identical images. Nothing is deleted or moved.

    Exact duplicates share a sha256 and are matched across the whole collection,
    because a byte-identical file really is the same file twice.

    Near duplicates are matched only within the same month. Bursts and re-saves
    happen minutes apart, not seasons apart, and two structurally similar photos
    from March and September are usually two real occasions rather than one
    redundant copy. Scoping this keeps the tool from quietly deleting a month's
    only picture because it rhymes with something from six months earlier.

    The first file in date order leads its group and is the only one eligible for
    representative selection.
    """
    by_sha: dict[str, str] = {}
    kept: dict[str, list[tuple[str, str]]] = {}  # month -> [(phash, rel)] leaders
    exact = near = 0

    for rec in sorted(records, key=lambda r: (r["date"], r["rel"])):
        if rec["sha256"] in by_sha:
            rec["duplicate_of"] = by_sha[rec["sha256"]]
            rec["duplicate_kind"] = "exact"
            exact += 1
            continue
        same_month = kept.setdefault(rec["month"], [])
        match = next((rel for ph, rel in same_month if hamming(ph, rec["phash"]) <= threshold), None)
        if match is not None:
            rec["duplicate_of"] = match
            rec["duplicate_kind"] = "near"
            near += 1
            continue
        rec["duplicate_of"] = None
        rec["duplicate_kind"] = None
        by_sha[rec["sha256"]] = rec["rel"]
        same_month.append((rec["phash"], rec["rel"]))

    return {"exact": exact, "near": near, "unique": len(records) - exact - near,
            "threshold": threshold}


# ---------------------------------------------------------------- timeline

def month_range(months: list[str]) -> list[str]:
    """Every month between the first and last, including the empty ones. The
    empty ones are the point: a gap only exists relative to a range."""
    if not months:
        return []
    start, end = min(months), max(months)
    y, m = int(start[:4]), int(start[5:7])
    ey, em = int(end[:4]), int(end[5:7])
    out = []
    while (y, m) <= (ey, em):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def pick_representatives(records: list[dict], month: str, limit: int, seed: int) -> list[dict]:
    """Choose up to `limit` non-duplicate photos spread across the month.

    Deterministic for a given (month, seed): sort by date, then take evenly
    spaced positions. Taking the first N alphabetically would return one morning
    of one day, which is how a report ends up looking like a single afternoon.
    """
    pool = [r for r in records if r["month"] == month and r["duplicate_of"] is None]
    pool.sort(key=lambda r: (r["date"], r["name"]))
    if len(pool) <= limit:
        return pool
    offset = seed % max(1, len(pool) // limit or 1)
    step = len(pool) / limit
    picked, used = [], set()
    for i in range(limit):
        idx = min(len(pool) - 1, int(i * step) + (offset if i else 0))
        while idx in used:
            idx = (idx + 1) % len(pool)
        used.add(idx)
        picked.append(pool[idx])
    return sorted(picked, key=lambda r: (r["date"], r["name"]))


def build_timeline(records: list[dict], max_per_month: int, seed: int) -> dict:
    counts = Counter(r["month"] for r in records)
    span = month_range(list(counts))
    per_month = {m: counts.get(m, 0) for m in span}
    non_zero = {m: c for m, c in per_month.items() if c}

    quiet = [m for m, c in per_month.items() if c == 0]
    dates = sorted(r["date"] for r in records)
    longest_gap, gap_span = 0, None
    for a, b in zip(dates, dates[1:]):
        delta = (dt.date.fromisoformat(b) - dt.date.fromisoformat(a)).days
        if delta > longest_gap:
            longest_gap, gap_span = delta, (a, b)

    avg = (sum(non_zero.values()) / len(non_zero)) if non_zero else 0
    busiest = sorted(non_zero.items(), key=lambda kv: (-kv[1], kv[0]))[:3]
    quietest = sorted(non_zero.items(), key=lambda kv: (kv[1], kv[0]))[:3]

    changes = []
    months_seen = list(per_month)
    for prev, cur in zip(months_seen, months_seen[1:]):
        changes.append({"month": cur, "delta": per_month[cur] - per_month[prev]})

    reps = {m: pick_representatives(records, m, max_per_month, seed) for m in non_zero}

    return {
        "months": span,
        "per_month": per_month,
        "quiet_months": quiet,
        "busiest_months": busiest,
        "quietest_months": quietest,
        "average_per_active_month": round(avg, 1),
        "longest_gap_days": longest_gap,
        "longest_gap_between": gap_span,
        "changes": changes,
        "representatives": reps,
        "date_range": {"start": dates[0], "end": dates[-1]} if dates else None,
    }


# ---------------------------------------------------------------- local vision

_model = None


def _load_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(MODEL_NAME)
    return _model


def cache_fingerprint(confidence: float, io_confidence: float) -> str:
    """Anything that would change a stored label goes into this fingerprint, so
    switching model, category list, prompts, or either threshold cannot silently
    reuse rows computed under different settings."""
    payload = json.dumps({
        "v": CACHE_VERSION,
        "model": MODEL_NAME,
        "categories": {k: CATEGORIES[k] for k in sorted(CATEGORIES)},
        "indoor_outdoor": {k: INDOOR_OUTDOOR[k] for k in sorted(INDOOR_OUTDOOR)},
        "confidence": round(float(confidence), 4),
        "io_confidence": round(float(io_confidence), 4),
    }, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _softmax(scores: list[float]) -> list[float]:
    top = max(scores)
    exps = [math.exp((s - top) * 100) for s in scores]  # 100 = CLIP logit scale
    total = sum(exps) or 1.0
    return [e / total for e in exps]


def _prototype(model, prompts: list[str]) -> list[float]:
    """Average the embeddings of several phrasings into one class prototype."""
    vecs = model.encode(prompts, normalize_embeddings=True)
    mean = [sum(col) / len(prompts) for col in zip(*vecs)]
    norm = math.sqrt(sum(v * v for v in mean)) or 1.0
    return [v / norm for v in mean]


def classify(paths: list[pathlib.Path], confidence: float,
             io_confidence: float) -> dict[str, dict]:
    """Zero-shot classify images with a local CLIP model.

    Returns {path: {category, category_confidence, indoor_outdoor, io_confidence}}.
    Below its threshold a label becomes "unclear" rather than being forced into
    the nearest bucket. Uncertainty is a result, not a failure.
    """
    model = _load_model()
    cat_keys = sorted(CATEGORIES)
    io_keys = sorted(INDOOR_OUTDOOR)
    cat_vecs = [_prototype(model, CATEGORIES[k]) for k in cat_keys]
    io_vecs = [_prototype(model, INDOOR_OUTDOOR[k]) for k in io_keys]

    out: dict[str, dict] = {}
    for path in paths:
        try:
            with Image.open(path) as img:
                img.load()
                oriented = ImageOps.exif_transpose(img).convert("RGB")
            vec = model.encode(oriented, normalize_embeddings=True)
        except Exception as e:
            out[str(path)] = {"category": "unclear", "category_confidence": 0.0,
                              "indoor_outdoor": "unclear", "io_confidence": 0.0,
                              "error": f"{type(e).__name__}"}
            continue

        cat_scores = [float(sum(a * b for a, b in zip(vec, cv))) for cv in cat_vecs]
        cat_probs = _softmax(cat_scores)
        best = max(range(len(cat_keys)), key=lambda i: cat_probs[i])
        io_scores = [float(sum(a * b for a, b in zip(vec, iv))) for iv in io_vecs]
        io_probs = _softmax(io_scores)
        io_best = max(range(len(io_keys)), key=lambda i: io_probs[i])

        out[str(path)] = {
            "category": cat_keys[best] if cat_probs[best] >= confidence else "unclear",
            "category_confidence": round(cat_probs[best], 3),
            "raw_category": cat_keys[best],
            "indoor_outdoor": io_keys[io_best] if io_probs[io_best] >= io_confidence else "unclear",
            "io_confidence": round(io_probs[io_best], 3),
        }
    return out


def aggregate_vision(records: list[dict]) -> dict:
    cats = Counter(r["vision"]["category"] for r in records if r.get("vision"))
    io = Counter(r["vision"]["indoor_outdoor"] for r in records if r.get("vision"))
    by_month = defaultdict(Counter)
    io_by_month = defaultdict(Counter)
    for r in records:
        if r.get("vision"):
            by_month[r["month"]][r["vision"]["category"]] += 1
            io_by_month[r["month"]][r["vision"]["indoor_outdoor"]] += 1
    return {
        "category_counts": dict(cats.most_common()),
        "indoor_outdoor": dict(io.most_common()),
        "category_by_month": {m: dict(c.most_common()) for m, c in sorted(by_month.items())},
        "indoor_outdoor_by_month": {m: dict(c.most_common()) for m, c in sorted(io_by_month.items())},
    }
