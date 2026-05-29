## domain/entities

Pydantic models đại diện cho các business objects cốt lõi. Tất cả `frozen=True` - immutable sau khi tạo. Muốn update field thì tạo instance mới, không mutate trực tiếp.

Entities không biết gì về DB, storage, hay HTTP. Chuyển đổi giữa entity và ORM model xảy ra ở infrastructure/repositories.

### Files

`document.py` - đại diện cho một file tài liệu trong hệ thống. Có sensitivity level, trạng thái xử lý, và path đến file trong storage.

`chunk.py` - một đoạn text được cắt từ document. Có `embedding_id` là None cho đến khi Qdrant assign point ID sau khi embed.

`user.py` - người dùng hệ thống. Không chứa password hash - việc đó thuộc về auth service ở application layer.

`ingest_job.py` - theo dõi tiến trình xử lý một document qua 7 bước pipeline. `total_chunks` và `embedded_chunks` dùng để tính % tiến độ.

`permission.py` - grant/restrict quyền truy cập document cho từng user. `expires_at = None` nghĩa là không hết hạn.

`review.py` - yêu cầu human review với document có sensitivity >= CONFIDENTIAL. `reviewer_id = None` khi chưa assign reviewer.
