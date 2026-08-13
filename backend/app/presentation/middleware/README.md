# presentation/middleware

## `rate_limit.py`

Per-IP sliding-window rate limit (in-memory, single-process — see file
comments for the multi-instance caveat). Applies to `/chat`, `/ingest`,
`/memory`, `/auth` — the routes that trigger real cost (LLM calls,
embedding jobs) or are auth-sensitive (login brute-force). Static assets and
cheap polling endpoints (`GET /ingest/jobs/{id}`, upload `POST`) are
excluded so bulk uploads and page loads can't exhaust the budget.

Budget: `RATE_LIMIT_PER_MINUTE` env var, default 30 requests/minute/IP.

CORS is still configured directly in `main.py`, not here.
