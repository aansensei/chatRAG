## presentation/api/metrics

Prometheus metrics exposure.

Sẽ có: `GET /metrics` trả Prometheus text format. Grafana scrape endpoint này theo interval. Custom metrics được định nghĩa ở `monitoring/metrics.py`.
