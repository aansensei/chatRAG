## application/ingestion

Use cases that orchestrate the ingestion pipeline.

### Files

`start_ingestion.py` - creates a new IngestJob for a document and publishes the `DocumentUploaded` event to kick off the pipeline. This is the first trigger point.

`retry_job.py` - retries an IngestJob in FAILED state. Resets to the step before the failure rather than restarting from scratch.
