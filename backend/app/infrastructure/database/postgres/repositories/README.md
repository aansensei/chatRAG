## infrastructure/database/postgres/repositories

Concrete repository implementations using SQLAlchemy async. Each file implements one interface from `domain/repositories/`.

Convention: receive a SQLAlchemy session via constructor, use ORM models to query, convert results to domain entities before returning.

### Files

`document_repo_impl.py` - implements `DocumentRepository`.

`user_repo_impl.py` - implements `UserRepository`.

`ingest_job_repo_impl.py` - implements `IngestJobRepository`.

`review_repo_impl.py` - implements `ReviewRepository`.
