"""Local embeddings.

Two backends, picked automatically:

1. sentence-transformers (all-MiniLM-L6-v2) if it is installed. Real,
   high-quality semantic embeddings that run fully on your machine.
2. A pure-Python hashing embedding fallback so this repo runs with zero
   installs. It is bag-of-words hashed into a fixed vector, then normalized.
   Good enough to demo retrieval; swap in sentence-transformers for real use.

Nothing here calls the network. Your documents never leave the machine.
"""

from __future__ import annotations

import hashlib
import math
import re

_DIM = 384  # matches all-MiniLM-L6-v2 so you can switch without reindexing

_model = None
_backend = None


def _load_model():
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
    return sum(x * y for x, y in zip(a, b))  # inputs are unit vectors
