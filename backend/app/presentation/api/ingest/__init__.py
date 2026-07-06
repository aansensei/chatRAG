import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.infrastructure.queue.redis.publisher import publish, set_job_status, get_job_status
from app.infrastructure.storage.local.rename_requests_store import (
    create_request, get_request, list_requests, resolve_request,
)
from app.infrastructure.vector.supabase.repository import (
    list_documents, delete_document, list_collections,
    rename_collection, delete_collection_docs, move_document_collection,
    get_document_file_path, relink_document_file, get_document_collection,
)
from app.presentation.api.auth import get_collections, get_current_user, require_admin_or_executive

router = APIRouter(prefix="/ingest", tags=["ingest"], dependencies=[Depends(get_current_user)])

STORAGE_PATH = Path(os.environ.get("LOCAL_STORAGE_PATH", "./storage"))
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".docx", ".xlsx", ".csv"}
MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_MB", "50")) * 1024 * 1024


def _department_of(collection: str) -> str:
    return collection.rsplit("/", 1)[-1]


def _has_kb_authority(user: dict, collection: str) -> bool:
    """Admins and Ban Giám đốc can add/delete anywhere. A department head can do
    the same, but only within their own department's folder — everyone else has
    to go through the request/approval flow instead."""
    if user["role"] == "admin" or user.get("department") == "Ban Giám đốc":
        return True
    return bool(user.get("is_department_head")) and user.get("department") == _department_of(collection)


@router.post("/upload")
async def upload(
    file: UploadFile = File(...),
    collection: str = Form(default="default"),
    user: dict = Depends(get_current_user),
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

    # Uploads go live immediately (no upload-blocking review), but anyone without
    # direct authority over this folder still needs someone to sign off after the
    # fact — rejecting removes the document again.
    if not _has_kb_authority(user, collection):
        create_request(user["id"], user["email"], "add", collection, document_id=document_id, filename=file.filename)

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
def delete_doc(document_id: str, user: dict = Depends(get_current_user)):
    collection = get_document_collection(document_id)
    # Fail closed if the document can't be found — admin-only in that edge case,
    # since there's no collection to check department authority against.
    if collection:
        if not _has_kb_authority(user, collection):
            raise HTTPException(status_code=403, detail="Không có quyền xóa trực tiếp — hãy gửi yêu cầu xóa")
    elif user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    delete_document(document_id)
    return {"ok": True}


@router.get("/collections")
def get_kb_collections():
    return list_collections()


class RenameCollectionBody(BaseModel):
    new_name: str


class MoveDocumentBody(BaseModel):
    collection: str


@router.patch("/collections/{name:path}")
def rename_collection_route(name: str, body: RenameCollectionBody, _user: dict = Depends(require_admin_or_executive)):
    if not body.new_name.strip():
        raise HTTPException(status_code=400, detail="new_name cannot be empty")
    rename_collection(name, body.new_name.strip())
    return {"ok": True}


@router.delete("/collections/{name:path}")
def delete_collection_route(name: str, user: dict = Depends(get_current_user)):
    if not _has_kb_authority(user, name):
        raise HTTPException(status_code=403, detail="Không có quyền xóa trực tiếp — hãy gửi yêu cầu xóa")
    delete_collection_docs(name)
    return {"ok": True}


@router.patch("/documents/{document_id}/collection")
def move_document_route(document_id: str, body: MoveDocumentBody):
    if not body.collection.strip():
        raise HTTPException(status_code=400, detail="collection cannot be empty")
    move_document_collection(document_id, body.collection.strip())
    return {"ok": True}


class RenameRequestBody(BaseModel):
    collection: str
    new_name: str


class DeleteRequestBody(BaseModel):
    collection: str
    document_id: str | None = None  # None means "delete the entire folder"
    filename: str | None = None


class RejectRequestBody(BaseModel):
    reason: str


@router.post("/rename-requests")
def create_rename_request(body: RenameRequestBody, user: dict = Depends(get_current_user)):
    if not body.new_name.strip():
        raise HTTPException(status_code=400, detail="new_name cannot be empty")
    return create_request(user["id"], user["email"], "rename", body.collection, new_name=body.new_name.strip())


@router.post("/delete-requests")
def create_delete_request(body: DeleteRequestBody, user: dict = Depends(get_current_user)):
    return create_request(user["id"], user["email"], "delete", body.collection, document_id=body.document_id, filename=body.filename)


@router.get("/rename-requests")
def get_kb_requests(user: dict = Depends(get_current_user)):
    # Admins and Ban Giám đốc see every request. A department head additionally
    # sees every request for their own department (not just ones they filed).
    # Everyone else only sees their own, to check on status/reason.
    is_admin_reviewer = user["role"] == "admin" or user.get("department") == "Ban Giám đốc"
    if is_admin_reviewer:
        return list_requests()
    own = list_requests(requester_id=user["id"])
    if not user.get("is_department_head"):
        return own
    dept = user.get("department")
    all_requests = list_requests()
    own_ids = {r["id"] for r in own}
    return own + [r for r in all_requests if r["id"] not in own_ids and _department_of(r["collection"]) == dept]


def _require_reviewer(user: dict, req: dict) -> None:
    if not _has_kb_authority(user, req["collection"]):
        raise HTTPException(status_code=403, detail="Không có quyền duyệt yêu cầu này")


@router.post("/rename-requests/{request_id}/approve")
def approve_kb_request(request_id: str, user: dict = Depends(get_current_user)):
    req = get_request(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req["status"] != "pending":
        raise HTTPException(status_code=409, detail="Request already resolved")
    if req["request_type"] == "rename":
        if user["role"] != "admin" and user.get("department") != "Ban Giám đốc":
            raise HTTPException(status_code=403, detail="Admin or Ban Giám đốc access required")
        rename_collection(req["collection"], req["new_name"])
    elif req["request_type"] == "delete":
        _require_reviewer(user, req)
        if req["document_id"]:
            delete_document(req["document_id"])
        else:
            delete_collection_docs(req["collection"])
    elif req["request_type"] == "add":
        _require_reviewer(user, req)
        # Already live since upload time — approving just confirms it stays.
    return resolve_request(request_id, "approved", user["id"])


@router.post("/rename-requests/{request_id}/reject")
def reject_kb_request(request_id: str, body: RejectRequestBody, user: dict = Depends(get_current_user)):
    if not body.reason.strip():
        raise HTTPException(status_code=400, detail="reason cannot be empty")
    req = get_request(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req["status"] != "pending":
        raise HTTPException(status_code=409, detail="Request already resolved")
    if req["request_type"] == "rename":
        if user["role"] != "admin" and user.get("department") != "Ban Giám đốc":
            raise HTTPException(status_code=403, detail="Admin or Ban Giám đốc access required")
    else:
        _require_reviewer(user, req)
        if req["request_type"] == "add" and req["document_id"]:
            # The document already went live at upload time — rejecting undoes that.
            delete_document(req["document_id"])
    return resolve_request(request_id, "rejected", user["id"], body.reason.strip())


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
