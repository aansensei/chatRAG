import os

# huggingface_hub reads HF_HUB_OFFLINE once at import time and caches it as a
# module constant — setting it later (e.g. inside a function, after
# sentence_transformers is already imported) has no effect. Once a model is
# cached locally, being "online" still costs ~15-20s of HF Hub freshness-check
# requests on every process start; skip them by default. If the model isn't
# cached yet (first-ever run), unset this env var once to let it download,
# then it can stay on for every run after.
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import httpx
from sentence_transformers import SentenceTransformer

from app.domain.entities.chunk import Chunk

_MODEL_CACHE: dict[str, SentenceTransformer] = {}

_EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
_OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

# Models served via Ollama's /api/embeddings endpoint instead of sentence-transformers
_OLLAMA_EMBED_MODELS = {"nomic-embed-text", "mxbai-embed-large", "all-minilm"}


def _get_st_model(model_name: str) -> SentenceTransformer:
    if model_name not in _MODEL_CACHE:
        # Unset (the common case): let sentence-transformers auto-detect and use
        # the GPU — this is the embedding_worker process, doing bulk document
        # embedding where GPU throughput matters. Explicitly set to "cpu" only in
        # the main API process (see main.py) — it embeds one short query string
        # per chat request, where CPU latency is a rounding error next to LLM
        # generation time, and it's not worth a second full model copy competing
        # for VRAM with the worker's copy on a GPU this small.
        device = os.environ.get("EMBEDDING_DEVICE") or None
        _MODEL_CACHE[model_name] = SentenceTransformer(model_name, device=device)
    return _MODEL_CACHE[model_name]


def _embed_ollama(text: str, model: str) -> list[float]:
    resp = httpx.post(
        f"{_OLLAMA_URL}/api/embeddings",
        json={"model": model, "prompt": text},
        timeout=httpx.Timeout(connect=5.0, read=30.0, write=5.0, pool=5.0),
    )
    resp.raise_for_status()
    return resp.json()["embedding"]


def embed_text(text: str, model_name: str | None = None) -> list[float]:
    model = model_name or _EMBEDDING_MODEL
    if model in _OLLAMA_EMBED_MODELS:
        return _embed_ollama(text, model)
    return _get_st_model(model).encode(text).tolist()


def embed_chunks(
    chunks: list[Chunk],
    model_name: str | None = None,
    batch_size: int = 64,
) -> list[list[float]]:
    if not chunks:
        return []

    model = model_name or _EMBEDDING_MODEL
    texts = [chunk.content for chunk in chunks]

    if model in _OLLAMA_EMBED_MODELS:
        return [_embed_ollama(t, model) for t in texts]

    st_model = _get_st_model(model)
    vectors = st_model.encode(texts, batch_size=batch_size, show_progress_bar=False)
    return [v.tolist() for v in vectors]
