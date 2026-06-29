import os

from supabase import Client, create_client


def _get_client() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_KEY"]
    return create_client(url, key)


def upsert_chunks(rows: list[dict]) -> None:
    """
    rows: list of dicts with keys:
      id, document_id, chunk_index, content, section_title, token_count, metadata, embedding
    """
    _get_client().table("chunks").upsert(rows).execute()


def search_chunks(
    query_vector: list[float],
    match_count: int = 15,
    threshold: float = 0.3,
) -> list[dict]:
    result = _get_client().rpc(
        "match_chunks",
        {
            "query_embedding": query_vector,
            "match_threshold": threshold,
            "match_count": match_count,
        },
    ).execute()
    return result.data
