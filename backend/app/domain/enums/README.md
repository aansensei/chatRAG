## domain/enums

Shared enums used across entities and services. All extend `(str, Enum)` to serialize as strings rather than integers in JSON and Pydantic — important for database storage and API responses.

### Files

`job_status.py` - statuses for the pipeline and review workflow.

- `IngestJobStatus`: PENDING → EXTRACTING → CHUNKING → EMBEDDING → INDEXING → COMPLETED (or FAILED at any step)
- `ReviewStatus`: PENDING / APPROVED / REJECTED for human review

`sensitivity.py` - classification and status enums related to documents.

- `SensitivityLevel`: PUBLIC < INTERNAL < CONFIDENTIAL < SECRET — determines the processing path (CONFIDENTIAL+ requires mandatory review)
- `DocumentStatus`: PROCESSING → READY (or FAILED / ARCHIVED)
- `UserRole`: ADMIN / USER / VIEWER — used to guard routes in the presentation layer
