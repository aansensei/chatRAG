"""BGE cross-encoder reranker.

Loads `BAAI/bge-reranker-v2-m3` lazily on first call. Returns chunks sorted by
relevance with their original `similarity` overwritten by the reranker score.
Falls back to identity if the model can't load.
"""
import logging
import os
import threading
from typing import Any

logger = logging.getLogger(__name__)

_MODEL_NAME = os.environ.get("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")
_TOP_N = int(os.environ.get("RERANKER_TOP_N", "8"))
_RELEVANCE_THRESHOLD = float(os.environ.get("RERANKER_THRESHOLD", "-2.0"))

_model = None
_model_lock = threading.Lock()
_load_failed = False


def _load():
    global _model, _load_failed
    if _model is not None or _load_failed:
        return _model
    with _model_lock:
        if _model is not None or _load_failed:
            return _model
        try:
            from sentence_transformers import CrossEncoder
            logger.info(f"Loading reranker: {_MODEL_NAME}")
            _model = CrossEncoder(_MODEL_NAME, max_length=512)
            logger.info("Reranker ready.")
        except Exception as exc:
            logger.warning(f"Reranker disabled — load failed: {exc}")
            _load_failed = True
    return _model


def rerank(query: str, chunks: list[dict[str, Any]], top_n: int | None = None) -> list[dict[str, Any]]:
    """Sort chunks by reranker score, keep top_n. Drops chunks below threshold."""
    if not chunks:
        return chunks
    model = _load()
    if model is None:
        return chunks
    pairs = [(query, (c.get("content") or "")[:1500]) for c in chunks]
    try:
        scores = model.predict(pairs)
    except Exception as exc:
        logger.warning(f"Reranker predict failed: {exc}")
        return chunks
    scored = list(zip(chunks, scores))
    scored.sort(key=lambda x: float(x[1]), reverse=True)
    for c, s in scored:
        c["similarity"] = float(s)
    out = [c for c, s in scored if float(s) >= _RELEVANCE_THRESHOLD]
    n = top_n or _TOP_N
    return out[:n] if out else [c for c, _ in scored[:n]]
