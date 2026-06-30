# shared

Cross-cutting utilities. Only `utils/` has real code today.

| Folder | Status |
|---|---|
| `utils/` | **Active** — embedders, extractors, chunkers |
| `config/` | Empty (env vars read inline via `os.environ`) |
| `exceptions/` | Empty |
| `logger/` | Empty (workers use `logging.basicConfig` inline) |
| `security/` | Empty (no JWT yet — see `presentation/api/auth/README.md`) |
