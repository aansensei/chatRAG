## application

Use cases layer. Mỗi folder là một bounded context, mỗi file là một use case. Không import trực tiếp từ infrastructure - chỉ dùng repository interfaces từ domain.

Use case nhận input, gọi repositories/services, publish events nếu cần, trả về result. Không có HTTP, không có SQL, không có ORM ở đây.

### Subdirectories

`auth/` - đăng nhập và JWT

`ingestion/` - khởi động và retry ingestion pipeline

`jobs/` - theo dõi trạng thái ingest job

`permission/` - validate quyền truy cập document

`retrieval/` - RAG pipeline: nhận câu hỏi, trả lời

`review/` - human review workflow cho sensitive documents
