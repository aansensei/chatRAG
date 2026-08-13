# presentation/api/metrics

Admin-only dashboards, backed by two append-only JSONL logs under
`storage/` (not a database — fine at this scale, would need one if the
files grow large or multiple processes need to write concurrently).

## Endpoints

All require admin (`Depends(require_admin)` on the router).

| Method | Path | Reads | Purpose |
|---|---|---|---|
| GET | `/metrics/summary` | `storage/metrics.jsonl` | Query volume, avg latency, error count, broken down by model and by user |
| GET | `/metrics/audit` | `storage/metrics.jsonl` | Query-level audit trail — who asked what, when, which documents were surfaced |
| GET | `/metrics/admin-audit` | `storage/admin_audit.jsonl` | Admin-action audit trail — who created/edited/deleted which user account, when |

`metrics.jsonl` entries are appended by `ask_question.py` after each chat
turn. `admin_audit.jsonl` entries are appended by
`app/infrastructure/storage/local/admin_audit_store.log_admin_action`,
called from the user-management endpoints in `presentation/api/auth`.

Not Prometheus-style `/metrics` scraping — this is a JSON API for the
in-app admin dashboard.
