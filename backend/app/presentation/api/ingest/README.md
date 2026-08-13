# presentation/api/ingest

Document upload, listing, deletion, and folder management. Also serves the
original file back for the in-app viewer.

---

## Endpoints

### Upload

| Method | Path | Purpose |
|---|---|---|
| POST | `/ingest/upload` | Upload a file. Multipart form with `file` and optional `collection` (default `"default"`). Returns `{job_id, document_id, status}`. Re-uploading a file with the same filename queues deletion of the stale version(s) once the new one finishes embedding (`replaces_document_ids`). |
| GET | `/ingest/jobs/{job_id}` | Poll job progress. Returns Redis hash: `status`, `step`, `progress`, `error`. |

### Documents

| Method | Path | Purpose |
|---|---|---|
| GET | `/ingest/documents` | List all docs visible to the caller. Filtered by API-key collections, or by `?collections=` query. |
| DELETE | `/ingest/documents/{id}` | Delete a doc and all its chunks. |
| GET | `/ingest/documents/{id}/file` | Serve the original file. PDF / image / CSV / TXT render inline; DOCX / XLSX download. |
| PATCH | `/ingest/documents/{id}/collection` | Move doc to another folder. Body: `{collection: string}`. |

### Folders (collections)

| Method | Path | Purpose |
|---|---|---|
| GET | `/ingest/collections` | List folders with doc counts (excludes `"default"`). |
| PATCH | `/ingest/collections/{name}` | Rename folder. Body: `{new_name: string}`. |
| DELETE | `/ingest/collections/{name}` | Delete folder AND all its docs/chunks. |

---

## Supported file types

`.pdf` `.docx` `.xlsx` `.csv` `.png` `.jpg` `.jpeg` `.tiff` `.bmp`

Rejected types return `400 File type {.ext} not supported`.

---

## File serving — inline vs download

`serve_document_file` returns the right `Content-Type` and disposition so the
browser handles each type correctly:

| Extensions | Content-Type | Disposition |
|---|---|---|
| pdf, png, jpg/jpeg, gif, webp, tiff, bmp, txt, csv | accurate mime | `inline` (renders in browser) |
| docx, xlsx | office mime | `attachment` (downloads) |
| anything else | `application/octet-stream` | `attachment` |

---

## Permissions

The handler depends on `get_collections` from `presentation/api/auth`, which
reads `X-API-Key` and returns the allowed folder list. In `DEV_MODE=true`
(default), it returns `[]` meaning "see everything".
