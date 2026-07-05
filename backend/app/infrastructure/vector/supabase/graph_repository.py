import time

import httpx

from .repository import _get_client

_RETRYABLE = (httpx.RemoteProtocolError, httpx.ConnectError, httpx.ReadTimeout)


def _with_retry(fn, attempts: int = 3, delay: float = 1.5):
    for i in range(attempts):
        try:
            return fn()
        except _RETRYABLE:
            if i == attempts - 1:
                raise
            time.sleep(delay * (i + 1))


def upsert_entity(collection: str, name: str, type_: str, description: str) -> str:
    """Insert or merge an entity by (collection, name). Returns the entity id."""
    client = _get_client()
    existing = _with_retry(
        lambda: client.table("graph_entities")
        .select("id, description")
        .eq("collection", collection)
        .eq("name", name)
        .limit(1)
        .execute()
        .data
    )
    if existing:
        entity_id = existing[0]["id"]
        if not existing[0].get("description") and description:
            _with_retry(
                lambda: client.table("graph_entities").update({"description": description}).eq("id", entity_id).execute()
            )
        return entity_id
    row = _with_retry(
        lambda: client.table("graph_entities")
        .insert({"collection": collection, "name": name, "type": type_, "description": description})
        .execute()
        .data
    )
    return row[0]["id"]


def insert_relation(
    collection: str,
    source_entity_id: str,
    target_entity_id: str,
    relation: str,
    description: str,
    chunk_id: str | None,
) -> None:
    client = _get_client()
    _with_retry(
        lambda: client.table("graph_relations")
        .upsert(
            {
                "collection": collection,
                "source_entity_id": source_entity_id,
                "target_entity_id": target_entity_id,
                "relation": relation,
                "description": description,
                "chunk_id": chunk_id,
            },
            on_conflict="source_entity_id,target_entity_id,relation,chunk_id",
        )
        .execute()
    )


def list_chunks_for_collection(collection: str, limit: int | None = None) -> list[dict]:
    client = _get_client()
    q = (
        client.table("chunks")
        .select("id, content, document_id, chunk_index")
        .eq("collection", collection)
        .order("document_id")
        .order("chunk_index")
    )
    if limit:
        q = q.limit(limit)
    else:
        q = q.limit(100000)
    return q.execute().data or []


def graph_stats(collection: str) -> dict:
    client = _get_client()
    entities = client.table("graph_entities").select("id", count="exact").eq("collection", collection).execute()
    relations = client.table("graph_relations").select("id", count="exact").eq("collection", collection).execute()
    return {"entities": entities.count or 0, "relations": relations.count or 0}


_SKIP_ENTITY_TYPES = {"date"}
_MIN_ENTITY_NAME_LEN = 3


def get_relevant_facts(question: str, collections: list[str], max_facts: int = 15) -> list[str]:
    """Cheap substring match of entity names against the question, then pull their
    1-hop relations — gives the LLM cross-document facts a single retrieved chunk
    wouldn't contain. Used by ask_question.py for collections with a pre-built graph.
    """
    client = _get_client()
    q_lower = question.lower()
    entities = (
        _with_retry(
            lambda: client.table("graph_entities")
            .select("id, name, type")
            .in_("collection", collections)
            .execute()
            .data
        )
        or []
    )
    matched_ids = [
        e["id"]
        for e in entities
        if e["type"] not in _SKIP_ENTITY_TYPES
        and len(e["name"]) >= _MIN_ENTITY_NAME_LEN
        and e["name"].lower() in q_lower
    ]
    if not matched_ids:
        return []

    by_id = {e["id"]: e["name"] for e in entities}
    id_list = ",".join(matched_ids)
    relations = (
        _with_retry(
            lambda: client.table("graph_relations")
            .select("source_entity_id, target_entity_id, relation")
            .in_("collection", collections)
            .or_(f"source_entity_id.in.({id_list}),target_entity_id.in.({id_list})")
            .limit(max_facts * 2)
            .execute()
            .data
        )
        or []
    )

    facts: list[str] = []
    seen: set[tuple[str, str, str]] = set()
    for r in relations:
        src = by_id.get(r["source_entity_id"], "?")
        tgt = by_id.get(r["target_entity_id"], "?")
        key = (src, r["relation"], tgt)
        if key in seen:
            continue
        seen.add(key)
        facts.append(f"{src} {r['relation']} {tgt}")
        if len(facts) >= max_facts:
            break
    return facts
