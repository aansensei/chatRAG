import os
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from app.infrastructure.queue.redis.publisher import publish, set_job_status, get_job_status

router = APIRouter(prefix="/ingest", tags=["ingest"])

STORAGE_PATH = Path(os.environ.get("LOCAL_STORAGE_PATH", "./storage"))
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"}


@router.post("/upload")
async def upload(
    file: UploadFile = File(...),
    collection: str = Form(default="default"),
):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type {ext} not supported")

    job_id = str(uuid.uuid4())
    document_id = str(uuid.uuid4())

    STORAGE_PATH.mkdir(parents=True, exist_ok=True)
    file_path = STORAGE_PATH / f"{job_id}{ext}"
    content = await file.read()
    file_path.write_bytes(content)

    set_job_status(job_id, status="queued", step="ocr")
    publish("queue:ocr", {
        "job_id": job_id,
        "document_id": document_id,
        "file_path": str(file_path),
        "collection": collection,
    })

    return {"job_id": job_id, "document_id": document_id, "status": "queued"}


@router.get("/jobs/{job_id}")
def job_status(job_id: str):
    status = get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status
