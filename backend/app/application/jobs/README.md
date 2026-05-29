## application/jobs

Use cases quản lý trạng thái ingest jobs.

### Files

`get_job_status.py` - lấy IngestJob theo id, trả về status và progress (embedded_chunks / total_chunks). Frontend dùng endpoint này để poll tiến trình upload.
