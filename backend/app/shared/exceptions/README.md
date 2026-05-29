## shared/exceptions

Custom exception classes shared across layers. Lets the presentation layer map exceptions to HTTP status codes cleanly instead of catching generic Exception.

Planned: `DocumentNotFound`, `PermissionDenied`, `UnsupportedFileType`, `IngestJobFailed`, `DuplicateDocument`, etc. Each exception carries a descriptive message for the error response.
