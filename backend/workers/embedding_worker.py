"""
Embedding worker — consumes from queue:embed, embeds chunks, upserts to Supabase.

Usage:
    python -m workers.embedding_worker
"""
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv; load_dotenv()

from app.application.graph.extract_graph import is_graph_enabled, extract_entities_relations
from app.domain.entities.chunk import Chunk
from app.infrastructure.queue.redis.consumer import consume
from app.infrastructure.queue.redis.publisher import set_job_status
from app.infrastructure.vector.supabase.graph_repository import insert_relation, upsert_entity
from app.infrastructure.vector.supabase.repository import upsert_chunks, delete_document
from app.shared.utils.embedders.text_embedder import embed_chunks

QUEUE_IN = "queue:embed"
_GRAPH_MODEL = "llama-3.3-70b-versatile"
_GRAPH_API_KEY = os.environ.get("GROQ_API_KEY")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [embedding_worker] %(message)s",
)
logger = logging.getLogger(__name__)


def _extract_graph_for_chunks(rows: list[dict], collection: str) -> None:
    """Keeps GraphRAG's entity/relationship graph in sync with newly-ingested
    chunks, for collections that have opted in. Best-effort — a failure here
    must never fail the ingest job, since the chunk is already embedded and
    usable for normal retrieval regardless of graph extraction succeeding.
    """
    if not is_graph_enabled(collection) or not _GRAPH_API_KEY:
        return
    for row in rows:
        try:
            entities, relations = extract_entities_relations(row["content"], _GRAPH_MODEL, _GRAPH_API_KEY)
            if not entities:
                continue
            name_to_id = {e["name"]: upsert_entity(collection, e["name"], e["type"], "") for e in entities}
            for r in relations:
                src_id = name_to_id.get(r["source"])
                tgt_id = name_to_id.get(r["target"])
                if src_id and tgt_id:
                    insert_relation(collection, src_id, tgt_id, r["relation"], r["description"], row["id"])
        except Exception:
            logger.exception(f"graph extraction failed for chunk {row.get('id')}")


def handle(message: dict) -> None:
    job_id = message["job_id"]
    raw_chunks = message["chunks"]
    source_metadata = message.get("source_metadata", {})

    logger.info(f"job={job_id} chunks={len(raw_chunks)}")
    set_job_status(job_id, status="embedding", step="embed", progress=60)

    try:
        chunks = [Chunk(**c) for c in raw_chunks]
        vectors = embed_chunks(chunks)

        total = len(chunks)
        collection = message.get("collection", "default")
        rows = []
        for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
            rows.append({
                "id": str(chunk.id),
                "document_id": str(chunk.document_id),
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "section_title": chunk.section_title,
                "token_count": chunk.token_count,
                "metadata": {
                    **source_metadata, **chunk.metadata,
                    **({"page_number": chunk.page_number} if chunk.page_number else {}),
                },
                "embedding": vector,
                "collection": collection,
            })
            pct = 60 + int((i + 1) / total * 35)
            set_job_status(job_id, status="embedding", progress=pct)

        upsert_chunks(rows)
        logger.info(f"job={job_id} upserted {len(rows)} chunks to Supabase")

        # Only retire previous versions now that the new one's chunks are
        # confirmed persisted — deleting them earlier risks leaving zero
        # copies of the document if this job had failed partway through.
        for old_id in message.get("replaces_document_ids") or []:
            delete_document(old_id)
            logger.info(f"job={job_id} retired stale version {old_id}")

        set_job_status(job_id, status="completed", step="done", progress=100)

        _extract_graph_for_chunks(rows, collection)

    except Exception:
        logger.exception(f"job={job_id} failed")
        set_job_status(job_id, status="failed", error="embedding failed")


if __name__ == "__main__":
    consume(QUEUE_IN, handle)
