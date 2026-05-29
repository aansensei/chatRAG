## monitoring

Observability setup. Prometheus cho metrics collection, Grafana cho visualization.

### Files

`metrics.py` - định nghĩa custom Prometheus metrics: số documents được ingest, latency của từng pipeline step, số RAG queries, error rates.

`prometheus.py` - Prometheus server config và middleware integration với FastAPI.

### Subdirectories

`grafana/` - Grafana dashboard JSON configs (chưa có nội dung).
