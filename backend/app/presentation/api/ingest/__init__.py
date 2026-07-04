import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.infrastructure.queue.redis.publisher import publish, set_job_status, get_job_status
from app.infrastructure.vector.supabase.repository import (
    list_documents, delete_document, list_collections,
    rename_collection, delete_collection_docs, move_document_collection,
    get_document_file_path, relink_document_file,
)
from app.presentation.api.auth import get_collections, get_current_user

router = APIRouter(prefix="/ingest", tags=["ingest"], dependencies=[Depends(get_current_user)])

STORAGE_PATH = Path(os.environ.get("LOCAL_STORAGE_PATH", "./storage"))
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".docx", ".xlsx", ".csv"}
MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_MB", "50")) * 1024 * 1024


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

    # Read in chunks and abort as soon as the cap is exceeded, instead of buffering
    # an arbitrarily large upload fully into memory before checking its size.
    content = bytearray()
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        content.extend(chunk)
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File quá lớn (giới hạn {MAX_UPLOAD_BYTES // (1024 * 1024)}MB)",
            )
    file_path.write_bytes(bytes(content))

    set_job_status(job_id, status="queued", step="ocr", progress=0)
    publish("queue:ocr", {
        "job_id": job_id,
        "document_id": document_id,
        "file_path": str(file_path),
        "original_filename": file.filename,
        "collection": collection,
    })

    return {"job_id": job_id, "document_id": document_id, "status": "queued"}


@router.get("/jobs/{job_id}")
def job_status(job_id: str):
    status = get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status


@router.delete("/jobs/{job_id}")
def cancel_job(job_id: str):
    status = get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    if status.get("status") in ("completed", "failed"):
        raise HTTPException(status_code=409, detail="Job already finished")
    set_job_status(job_id, status="failed", error="Cancelled by user")
    return {"ok": True}


@router.get("/documents")
def documents(collections: list[str] = Depends(get_collections)):
    return list_documents(collections or None)


@router.delete("/documents/{document_id}")
def delete_doc(document_id: str):
    delete_document(document_id)
    return {"ok": True}


@router.get("/collections")
def get_kb_collections():
    return list_collections()


class RenameCollectionBody(BaseModel):
    new_name: str


class MoveDocumentBody(BaseModel):
    collection: str


@router.patch("/collections/{name}")
def rename_collection_route(name: str, body: RenameCollectionBody):
    if not body.new_name.strip():
        raise HTTPException(status_code=400, detail="new_name cannot be empty")
    rename_collection(name, body.new_name.strip())
    return {"ok": True}


@router.delete("/collections/{name}")
def delete_collection_route(name: str):
    delete_collection_docs(name)
    return {"ok": True}


@router.patch("/documents/{document_id}/collection")
def move_document_route(document_id: str, body: MoveDocumentBody):
    if not body.collection.strip():
        raise HTTPException(status_code=400, detail="collection cannot be empty")
    move_document_collection(document_id, body.collection.strip())
    return {"ok": True}


_MIME_MAP = {
    ".pdf": "application/pdf",
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".tiff": "image/tiff", ".bmp": "image/bmp", ".gif": "image/gif",
    ".webp": "image/webp", ".txt": "text/plain; charset=utf-8",
    ".csv": "text/csv; charset=utf-8",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
_INLINE_EXTS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif", ".webp", ".txt", ".csv"}


@router.get("/documents/{document_id}/file")
def serve_document_file(document_id: str):
    file_path = get_document_file_path(document_id)
    if not file_path:
        raise HTTPException(status_code=410, detail="Source file was not preserved on upload — re-upload to enable viewing.")
    if not Path(file_path).exists():
        raise HTTPException(status_code=410, detail=f"File missing on disk: {Path(file_path).name}. Re-upload to restore.")
    p = Path(file_path)
    ext = p.suffix.lower()
    media_type = _MIME_MAP.get(ext, "application/octet-stream")
    disposition = "inline" if ext in _INLINE_EXTS else "attachment"
    safe_name = p.name.replace('"', '')
    headers = {"Content-Disposition": f'{disposition}; filename="{safe_name}"'}
    return FileResponse(path=file_path, filename=safe_name, media_type=media_type, headers=headers)


@router.post("/documents/{document_id}/relink")
async def relink_document(document_id: str, file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type {ext} not supported")
    STORAGE_PATH.mkdir(parents=True, exist_ok=True)
    safe_name = f"relink-{uuid.uuid4()}{ext}"
    new_path = STORAGE_PATH / safe_name
    new_path.write_bytes(await file.read())
    affected = relink_document_file(document_id, str(new_path))
    if affected == 0:
        new_path.unlink(missing_ok=True)
        raise HTTPException(status_code=404, detail="Document not found")
    return {"ok": True, "chunks_updated": affected, "file_path": str(new_path)}
