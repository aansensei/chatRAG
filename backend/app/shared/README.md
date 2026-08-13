# shared

Cross-cutting utilities.

| Folder | Status |
|---|---|
| `utils/` | **Active** — embedders, extractors, chunkers |
| `security/` | **Active** — `permissions.py` (department ACL checks). JWT encode/decode itself lives inline in `presentation/api/auth/__init__.py`, not here. |
| `config/` | Empty (env vars read inline via `os.environ`) |
| `exceptions/` | Empty |
| `logger/` | Empty (workers use `logging.basicConfig` inline) |
