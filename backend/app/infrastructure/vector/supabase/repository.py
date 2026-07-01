import os

from supabase import Client, create_client


def _get_client() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_KEY"]
    return create_client(url, key)


def list_collections() -> list[dict]:
    client = _get_client()
    result = client.table("chunks").select("collection, document_id").limit(10000).execute()
    cols: dict[str, set] = {}
    for row in result.data:
        col = row.get("collection") or "default"
        doc_id = row.get("document_id", "")
        if col not in cols:
            cols[col] = set()
        if doc_id:
            cols[col].add(doc_id)
    return [{"name": k, "doc_count": len(v)} for k, v in sorted(cols.items()) if k != "default"]


def rename_collection(old_name: str, new_name: str) -> None:
    _get_client().table("chunks").update({"collection": new_name}).eq("collection", old_name).execute()


def delete_collection_docs(name: str) -> None:
    _get_client().table("chunks").delete().eq("collection", name).execute()


def move_document_collection(document_id: str, new_collection: str) -> None:
    _get_client().table("chunks").update({"collection": new_collection}).eq("document_id", document_id).execute()


def list_documents(collections: list[str] | None = None) -> list[dict]:
    from pathlib import Path as _P
    q = _get_client().table("chunks").select("document_id, metadata, chunk_index, collection").order("chunk_index").limit(10000)
    if collections:
        q = q.in_("collection", collections)
    result = q.execute()
    seen: dict[str, dict] = {}
    for row in result.data:
        doc_id = row["document_id"]
        if doc_id not in seen:
            meta = row.get("metadata") or {}
            fp = meta.get("file_path") or ""
            has_file = bool(fp) and _P(fp).exists()
            seen[doc_id] = {
                "document_id": doc_id,
                "source": meta.get("source", ""),
                "file_path": fp,
                "has_file": has_file,
                "pages": meta.get("pages"),
                "collection": row.get("collection", "default"),
                "chunk_count": 0,
            }
        seen[doc_id]["chunk_count"] += 1
    return list(seen.values())


def relink_document_file(document_id: str, new_file_path: str) -> int:
    """Update metadata.file_path for all chunks of document_id. Returns affected rows."""
    client = _get_client()
    rows = client.table("chunks").select("id, metadata").eq("document_id", document_id).execute().data or []
    if not rows:
        return 0
    for r in rows:
        meta = r.get("metadata") or {}
        meta["file_path"] = new_file_path
        client.table("chunks").update({"metadata": meta}).eq("id", r["id"]).execute()
    return len(rows)


def delete_document(document_id: str) -> None:
    _get_client().table("chunks").delete().eq("document_id", document_id).execute()


def get_document_file_path(document_id: str) -> str | None:
    result = (
        _get_client().table("chunks")
        .select("metadata")
        .eq("document_id", document_id)
        .limit(1)
        .execute()
    )
    if result.data:
        meta = result.data[0].get("metadata") or {}
        return meta.get("file_path") or None
    return None


def upsert_chunks(rows: list[dict]) -> None:
    """
    rows: list of dicts with keys:
      id, document_id, chunk_index, content, section_title, token_count, metadata, embedding
    """
    _get_client().table("chunks").upsert(rows).execute()


def filename_search_chunks(
    name_tokens: list[str],
    collections: list[str] | None = None,
) -> list[dict]:
    """
    Fetch chunks from documents whose filename (metadata->source) matches a token.
    Tries tokens from most specific (longest) to least specific (shortest).
    Stops at the first token that returns results to avoid mixing unrelated docs.
    E.g. 'Cam7 test 2 writing task 2' is tried before 'Cam7', so only the
    specific file is returned, not all Cam7 documents.
    """
    client = _get_client()
    for token in sorted(set(name_tokens), key=len, reverse=True):
        if len(token) < 3:
            continue
        q = (
            client.table("chunks")
            .select("id, document_id, chunk_index, content, section_title, metadata, collection")
            .filter("metadata->>source", "ilike", f"%{token}%")
            .order("chunk_index")
            .limit(500)
        )
        if collections:
            q = q.in_("collection", collections)
        rows = q.execute().data or []
        if not rows:
            continue
        results = []
        seen_ids: set = set()
        for row in rows:
            chunk_id = row.get("id")
            if chunk_id and chunk_id not in seen_ids:
                row["similarity"] = 0.88
                results.append(row)
                seen_ids.add(chunk_id)
        return results
    return []


def keyword_search_chunks(
    keywords: list[str],
    match_count: int = 6,
    collections: list[str] | None = None,
) -> list[dict]:
    """Full-text ilike search for exact codes/identifiers that semantic search misses."""
    client = _get_client()
    results = []
    seen_ids: set = set()
    for kw in keywords:
        if len(kw) < 3:
            continue
        q = client.table("chunks").select(
            "id, document_id, chunk_index, content, section_title, metadata, collection"
        ).ilike("content", f"%{kw}%").limit(match_count)
        if collections:
            q = q.in_("collection", collections)
        rows = q.execute().data or []
        for row in rows:
            if row.get("id") not in seen_ids:
                row["similarity"] = 0.5
                results.append(row)
                seen_ids.add(row["id"])
    return results


def search_chunks(
    query_vector: list[float],
    match_count: int = 15,
    threshold: float = 0.3,
    collections: list[str] | None = None,
) -> list[dict]:
    params = {
        "query_embedding": query_vector,
        "match_threshold": threshold,
        "match_count": match_count,
        "filter_collections": collections if collections else None,
    }
    client = _get_client()
    result = client.rpc("match_chunks", params).execute()
    hits = result.data
    if not hits:
        return hits or []

    # Enforce collection filter client-side — defense against the RPC ignoring it.
    if collections:
        hit_doc_ids = list({h.get("document_id") for h in hits if h.get("document_id")})
        if hit_doc_ids:
            allowed_rows = (
                client.table("chunks")
                .select("document_id")
                .in_("collection", collections)
                .in_("document_id", hit_doc_ids)
                .limit(len(hit_doc_ids))
                .execute()
            )
            allowed = {r["document_id"] for r in (allowed_rows.data or [])}
            hits = [h for h in hits if h.get("document_id") in allowed]
        if not hits:
            return []

    # Expand hits: for each hit, fetch all chunks in the same section (same doc + section_title).
    # Falls back to fetching neighbors (+1..+5) when section_title is None.
    existing_ids = {c.get("id") for c in hits if c.get("id")}
    extras: list[dict] = []

    # Group hits by (doc_id, section_title) to batch section fetches
    section_keys: set[tuple[str, str]] = set()
    fallback_ids: set[tuple[str, int]] = set()

    for c in hits:
        doc_id = c.get("document_id")
        section = c.get("section_title")
        idx = c.get("chunk_index")
        if doc_id and section:
            section_keys.add((doc_id, section))
        elif doc_id and idx is not None:
            for offset in range(1, 6):
                fallback_ids.add((doc_id, idx + offset))

    for doc_id, section in section_keys:
        r = (
            client.table("chunks")
            .select("id, document_id, chunk_index, content, section_title, metadata, collection")
            .eq("document_id", doc_id)
            .eq("section_title", section)
            .order("chunk_index")
            .execute()
        )
        for row in r.data:
            if row.get("id") not in existing_ids:
                row["similarity"] = 0.0
                extras.append(row)
                existing_ids.add(row["id"])

    for doc_id, idx in fallback_ids:
        if any(c.get("document_id") == doc_id and c.get("chunk_index") == idx for c in hits + extras):
            continue
        r = (
            client.table("chunks")
            .select("id, document_id, chunk_index, content, section_title, metadata, collection")
            .eq("document_id", doc_id)
            .eq("chunk_index", idx)
            .execute()
        )
        for row in r.data:
            if row.get("id") not in existing_ids:
                row["similarity"] = 0.0
                extras.append(row)
                existing_ids.add(row["id"])

    return hits + extras
