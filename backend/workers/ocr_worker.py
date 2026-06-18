"""
OCR worker — consumes from queue:ocr, runs OCR, pushes extracted text to queue:chunk.

Usage:
    python -m workers.ocr_worker
"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.infrastructure.queue.redis.consumer import consume
from app.infrastructure.queue.redis.publisher import publish, set_job_status

QUEUE_IN = "queue:ocr"
QUEUE_OUT = "queue:chunk"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [ocr_worker] %(message)s",
)
logger = logging.getLogger(__name__)


def handle(message: dict) -> None:
    job_id = message["job_id"]
    document_id = message["document_id"]
    file_path = message["file_path"]
    languages = message.get("languages", ["en", "vi"])

    logger.info(f"job={job_id} file={file_path}")
    set_job_status(job_id, status="extracting", step="ocr")

    try:
        from app.shared.utils.extractors.ocr_extractor import extract_ocr_image, extract_ocr_pdf

        ext = Path(file_path).suffix.lower()
        if ext == ".pdf":
            result = extract_ocr_pdf(file_path, languages)
        else:
            result = extract_ocr_image(file_path, languages)

        logger.info(f"job={job_id} extracted {len(result.text)} chars")
        set_job_status(job_id, status="chunking", step="chunk")

        publish(QUEUE_OUT, {
            "job_id": job_id,
            "document_id": document_id,
            "text": result.text,
            "metadata": result.metadata,
        })

    except Exception as exc:
        logger.exception(f"job={job_id} failed")
        set_job_status(job_id, status="failed", error=str(exc))


if __name__ == "__main__":
    consume(QUEUE_IN, handle)
