"""
OCR worker — consumes from queue:ocr, runs OCR, pushes extracted text to queue:chunk.

Usage:
    python -m workers.ocr_worker
"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv; load_dotenv()

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
    set_job_status(job_id, status="extracting", step="ocr", progress=5)

    try:
        from app.shared.utils.extractors.ocr_extractor import extract_ocr_image, extract_ocr_pdf
        from app.shared.utils.extractors.office_extractor import extract_docx, extract_xlsx

        def on_page(done: int, total: int) -> None:
            pct = 5 + int(done / total * 45)
            set_job_status(job_id, status="extracting", progress=pct)

        from app.shared.utils.extractors.office_extractor import extract_csv
        ext = Path(file_path).suffix.lower()
        if ext == ".pdf":
            result = extract_ocr_pdf(file_path, languages, on_page_done=on_page)
        elif ext == ".docx":
            result = extract_docx(file_path)
        elif ext in (".xlsx",):
            result = extract_xlsx(file_path)
        elif ext == ".csv":
            result = extract_csv(file_path)
        else:
            result = extract_ocr_image(file_path, languages)

        logger.info(f"job={job_id} extracted {len(result.text)} chars")
        set_job_status(job_id, status="chunking", step="chunk", progress=50)

        original_filename = message.get("original_filename") or Path(file_path).name
        metadata = {
            **(result.metadata or {}),
            "source": original_filename,
            "file_path": file_path,
            "sensitivity": message.get("sensitivity", "internal"),
            "content_hash": message.get("content_hash"),
        }

        publish(QUEUE_OUT, {
            "job_id": job_id,
            "document_id": document_id,
            "text": result.text,
            "metadata": metadata,
            "collection": message.get("collection", "default"),
            "replaces_document_ids": message.get("replaces_document_ids") or [],
        })

    except Exception as exc:
        logger.exception(f"job={job_id} failed")
        set_job_status(job_id, status="failed", error=str(exc))


if __name__ == "__main__":
    consume(QUEUE_IN, handle)
