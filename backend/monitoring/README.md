## monitoring

Observability setup. Prometheus for metrics collection, Grafana for visualization.

### Files

`metrics.py` - defines custom Prometheus metrics: documents ingested, latency per pipeline step, RAG query count, error rates.

`prometheus.py` - Prometheus server config and FastAPI middleware integration.

### Subdirectories

`grafana/` - Grafana dashboard JSON configs (not yet populated).
