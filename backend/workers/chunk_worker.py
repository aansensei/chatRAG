"""
Chunk worker — consumes from queue:chunk, splits text into chunks, pushes to queue:embed.

Usage:
    python -m workers.chunk_worker
"""
import logging
import sys
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv; load_dotenv()

from app.infrastructure.queue.redis.consumer import consume
from app.infrastructure.queue.redis.publisher import publish, set_job_status
from app.shared.utils.chunkers import ChunkConfig, chunk_text

QUEUE_IN = "queue:chunk"
QUEUE_OUT = "queue:embed"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [chunk_worker] %(message)s",
)
logger = logging.getLogger(__name__)


def handle(message: dict) -> None:
    job_id = message["job_id"]
    document_id = message["document_id"]
    text = message["text"]

    logger.info(f"job={job_id} text={len(text)} chars")
    set_job_status(job_id, status="chunking", step="chunk", progress=40)

    try:
        chunks = chunk_text(text, UUID(document_id), ChunkConfig())

        logger.info(f"job={job_id} produced {len(chunks)} chunks")
        set_job_status(job_id, status="embedding", step="embed", progress=55)

        publish(QUEUE_OUT, {
            "job_id": job_id,
            "document_id": document_id,
            "chunks": [c.model_dump(mode="json") for c in chunks],
            "source_metadata": message.get("metadata", {}),
            "collection": message.get("collection", "default"),
        })

    except Exception as exc:
        logger.exception(f"job={job_id} failed")
        set_job_status(job_id, status="failed", error=str(exc))


if __name__ == "__main__":
    consume(QUEUE_IN, handle)
