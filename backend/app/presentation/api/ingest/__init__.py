import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from app.infrastructure.queue.redis.publisher import publish, set_job_status, get_job_status
from app.infrastructure.vector.supabase.repository import (
    list_documents, delete_document, list_collections,
    rename_collection, delete_collection_docs, move_document_collection,
)
from app.presentation.api.auth import get_collections

router = APIRouter(prefix="/ingest", tags=["ingest"])

STORAGE_PATH = Path(os.environ.get("LOCAL_STORAGE_PATH", "./storage"))
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".docx", ".xlsx"}


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
