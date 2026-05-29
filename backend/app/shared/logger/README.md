## shared/logger

Logging setup. Dùng structured JSON logging để dễ parse bằng Grafana Loki hoặc các log aggregation tools.

Sẽ có: `setup_logging()` function, logger factory theo module name. Log format bao gồm timestamp, level, module, message, và extra fields (request_id, user_id, document_id khi có).
