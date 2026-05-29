## domain/entities

Pydantic models representing core business objects. All are `frozen=True` — immutable after creation. To update a field, create a new instance rather than mutating in place.

Entities have no knowledge of the database, storage, or HTTP. Conversion between entities and ORM models happens in infrastructure/repositories.

### Files

`document.py` - a file document in the system. Carries sensitivity level, processing status, and a relative storage path.

`chunk.py` - a text segment cut from a document. `embedding_id` is None until Qdrant assigns a point ID after embedding.

`user.py` - a system user. Does not contain the password hash — that belongs in the auth service.

`ingest_job.py` - tracks progress of a document through the 7-step pipeline. `total_chunks` and `embedded_chunks` are used to compute percentage progress.

`permission.py` - grants or restricts a user's access to a specific document. `expires_at = None` means the permission never expires.

`review.py` - a human review request for documents with sensitivity >= CONFIDENTIAL. `reviewer_id = None` when no reviewer has been assigned yet.
