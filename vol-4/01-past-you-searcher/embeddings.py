"""Local embeddings for Past-You Searcher.

Two backends, picked automatically at import time:

1. sentence-transformers (all-MiniLM-L6-v2) when it is installed. Real semantic
   embeddings, running on your machine. The model downloads once (~90MB) on
   first use and is cached by the library afterwards.
2. A pure-Python hashing embedding, used when sentence-transformers is not
   installed. It is bag-of-words hashed into a fixed vector and normalized. It
   matches on shared words rather than meaning, so results are noticeably
   weaker, but it needs zero installs and proves the pipeline end to end.

Nothing in this file touches the network except the one-time model download in
backend 1. Your writing is never sent anywhere from here.

The index records which backend produced it. Vectors from the two backends are
not comparable, so ingest.py rebuilds automatically when the backend changes.
"""

from __future__ import annotations

import hashlib
import math
import re

_DIM = 384  # matches all-MiniLM-L6-v2

_model = None
_backend: str | None = None


def _load_model() -> None:
    global _model, _backend
    if _backend is not None:
        return
    try:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer("all-MiniLM-L6-v2")
        _backend = "sentence-transformers"
    except Exception:
        _model = None
        _backend = "hashing"


def backend_name() -> str:
    _load_model()
    assert _backend is not None
    return _backend


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _hash_embed(text: str) -> list[float]:
    vec = [0.0] * _DIM
    for tok in _tokenize(text):
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
        idx = h % _DIM
        sign = 1.0 if (h >> 8) & 1 else -1.0
        vec[idx] += sign
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def embed(texts: list[str]) -> list[list[float]]:
    """Embed a list of strings into a list of unit vectors."""
    _load_model()
    if _backend == "sentence-transformers":
        return [v.tolist() for v in _model.encode(texts, normalize_embeddings=True)]
    return [_hash_embed(t) for t in texts]


def cosine(a: list[float], b: list[float]) -> float:
    """Both inputs are unit vectors, so the dot product is the cosine."""
    return sum(x * y for x, y in zip(a, b))
