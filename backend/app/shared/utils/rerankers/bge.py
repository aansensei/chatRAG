"""FlashRank reranker — replaces slow BGE cross-encoder (22s) with ~31ms CPU reranking."""
import logging
import os
import threading
from typing import Any

logger = logging.getLogger(__name__)

_TOP_N = int(os.environ.get("RERANKER_TOP_N", "8"))
_MODEL_NAME = os.environ.get("RERANKER_MODEL", "ms-marco-TinyBERT-L-2-v2")

_ranker = None
_lock = threading.Lock()
_load_failed = False


def _load():
    global _ranker, _load_failed
    if _ranker is not None or _load_failed:
        return _ranker
    with _lock:
        if _ranker is not None or _load_failed:
            return _ranker
        try:
            from flashrank import Ranker
            logger.info("Loading FlashRank reranker: %s", _MODEL_NAME)
            _ranker = Ranker(model_name=_MODEL_NAME)
            logger.info("FlashRank reranker ready.")
        except Exception as exc:
            logger.warning("FlashRank disabled — load failed: %s", exc)
            _load_failed = True
    return _ranker


def rerank(query: str, chunks: list[dict[str, Any]], top_n: int | None = None) -> list[dict[str, Any]]:
    if not chunks:
        return chunks
    ranker = _load()
    if ranker is None:
        return chunks
    try:
        from flashrank import RerankRequest
        passages = [{"id": i, "text": (c.get("content") or "")[:1500]} for i, c in enumerate(chunks)]
        results = ranker.rerank(RerankRequest(query=query, passages=passages))
        n = top_n or _TOP_N
        out = []
        for r in results[:n]:
            chunk = chunks[r["id"]].copy()
            chunk["similarity"] = float(r.get("score", 0.0))
            out.append(chunk)
        return out if out else chunks[:n]
    except Exception as exc:
        logger.warning("FlashRank predict failed: %s", exc)
        return chunks
