## presentation/api/metrics

Prometheus metrics exposure.

Planned: `GET /metrics` returns Prometheus text format. Grafana scrapes this endpoint on a configured interval. Custom metrics are defined in `monitoring/metrics.py`.
