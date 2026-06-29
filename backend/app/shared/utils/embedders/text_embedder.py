from sentence_transformers import SentenceTransformer

from app.domain.entities.chunk import Chunk

_MODEL_CACHE: dict[str, SentenceTransformer] = {}


def _get_model(model_name: str) -> SentenceTransformer:
    # cache model in memory — loading from disk is slow (~1s), reuse across calls
    if model_name not in _MODEL_CACHE:
        _MODEL_CACHE[model_name] = SentenceTransformer(model_name)
    return _MODEL_CACHE[model_name]


def embed_text(text: str, model_name: str = "all-MiniLM-L6-v2") -> list[float]:
    return _get_model(model_name).encode(text).tolist()


def embed_chunks(
    chunks: list[Chunk],
    model_name: str = "all-MiniLM-L6-v2",
    batch_size: int = 64,
) -> list[list[float]]:
    """
    Embed a list of chunks and return one vector per chunk.
    Vectors are in the same order as the input list.
    """
    if not chunks:
        return []

    model = _get_model(model_name)
    texts = [chunk.content for chunk in chunks]
    vectors = model.encode(texts, batch_size=batch_size, show_progress_bar=False)
    return [v.tolist() for v in vectors]
