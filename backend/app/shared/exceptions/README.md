## shared/exceptions

Custom exception classes dùng chung. Giúp presentation layer map exception → HTTP status code rõ ràng thay vì bắt generic Exception.

Sẽ có: `DocumentNotFound`, `PermissionDenied`, `UnsupportedFileType`, `IngestJobFailed`, `DuplicateDocument`, v.v. Mỗi exception có message rõ ràng cho error response.
