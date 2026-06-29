"""
Embedding worker — consumes from queue:embed, embeds chunks, upserts to Supabase.

Usage:
    python -m workers.embedding_worker
"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.domain.entities.chunk import Chunk
from app.infrastructure.queue.redis.consumer import consume
from app.infrastructure.queue.redis.publisher import set_job_status
from app.infrastructure.vector.supabase.repository import upsert_chunks
from app.shared.utils.embedders.text_embedder import embed_chunks

QUEUE_IN = "queue:embed"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [embedding_worker] %(message)s",
)
logger = logging.getLogger(__name__)


def handle(message: dict) -> None:
    job_id = message["job_id"]
    raw_chunks = message["chunks"]

    logger.info(f"job={job_id} chunks={len(raw_chunks)}")
    set_job_status(job_id, status="embedding", step="embed")

    try:
        chunks = [Chunk(**c) for c in raw_chunks]
        vectors = embed_chunks(chunks)

        rows = [
            {
                "id": str(chunk.id),
                "document_id": str(chunk.document_id),
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "section_title": chunk.section_title,
                "token_count": chunk.token_count,
                "metadata": chunk.metadata,
                "embedding": vector,
            }
            for chunk, vector in zip(chunks, vectors)
        ]

        upsert_chunks(rows)
        logger.info(f"job={job_id} upserted {len(rows)} chunks to Supabase")
        set_job_status(job_id, status="completed", step="done")

    except Exception:
        logger.exception(f"job={job_id} failed")
        set_job_status(job_id, status="failed", error="embedding failed")


if __name__ == "__main__":
    consume(QUEUE_IN, handle)
