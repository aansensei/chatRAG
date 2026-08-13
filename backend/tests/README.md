# tests

Pytest suite — runs in `.github/workflows/ci.yml` on every push/PR against a
clean runner (no live Supabase/Redis; standalone unit tests only).

`scripts/eval_retrieval.py` is a separate, heavier retrieval-quality eval
against a real Supabase instance and the golden-set KB documents — wired
into `.github/workflows/retrieval-eval.yml` (manual trigger + nightly cron,
not on every PR, since it needs live `SUPABASE_URL`/`SUPABASE_SERVICE_KEY`
secrets).
