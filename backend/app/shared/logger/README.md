## shared/logger

Logging setup. Uses structured JSON logging for easy parsing by Grafana Loki or other log aggregation tools.

Planned: `setup_logging()` function, logger factory by module name. Log format includes timestamp, level, module, message, and extra fields (request_id, user_id, document_id when available).
