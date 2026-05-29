## scheduler

Scheduled background tasks that run on a timer, not triggered by events. Uses APScheduler or celery-beat depending on config.

### Files

`bootstrap_ingestion.py` - runs once on first system startup to ingest all pre-existing documents.

`cleanup.py` - periodic cleanup: removes IngestJobs older than N days in COMPLETED/FAILED state, removes orphaned chunks with no parent document.

`delta_ingestion.py` - runs on a schedule, detects documents that changed since the last ingest (by hash or modified_at), and re-triggers ingestion for them.

`retry_failed_jobs.py` - automatically retries IngestJobs stuck in FAILED state after a backoff period. Capped at a maximum retry count to avoid infinite loops.
