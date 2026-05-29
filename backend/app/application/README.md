## application

Use cases layer. Each folder is a bounded context; each file is a single use case. Never imports directly from infrastructure — only uses repository interfaces from domain.

A use case receives input, calls repositories or services, publishes events if needed, and returns a result. No HTTP, no SQL, no ORM here.

### Subdirectories

`auth/` - login and JWT issuance

`ingestion/` - start and retry the ingestion pipeline

`jobs/` - track ingest job status

`permission/` - validate document access rights

`retrieval/` - RAG pipeline: receive a question, return an answer

`review/` - human review workflow for sensitive documents
