# application/jobs

Track ingest job status.

**Not implemented as use cases.** Job state is a Redis hash written by `infrastructure/queue/redis/publisher.set_job_status`; read by `GET /ingest/jobs/{id}`.
