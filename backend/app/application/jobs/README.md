## application/jobs

Use cases for ingest job management.

### Files

`get_job_status.py` - fetches an IngestJob by id and returns its status and progress (embedded_chunks / total_chunks). Used by the frontend to poll upload progress.
