## infrastructure/database/postgres/repositories

Concrete repository implementations dùng SQLAlchemy async. Mỗi file implement một interface từ `domain/repositories/`.

Quy tắc ở đây: nhận SQLAlchemy session qua constructor, dùng ORM models để query, convert kết quả về domain entities trước khi trả ra.

### Files

`document_repo_impl.py` - implements `DocumentRepository`.

`user_repo_impl.py` - implements `UserRepository`.

`ingest_job_repo_impl.py` - implements `IngestJobRepository`.

`review_repo_impl.py` - implements `ReviewRepository`.
