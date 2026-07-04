# infrastructure/storage/local

Local filesystem storage.

Uploaded file storage is inlined in `presentation/api/ingest/__init__.py` (`STORAGE_PATH`), not routed through this layer.

Chat session persistence lives here (`local_storage.py`): SQLite at `storage/chat_sessions.db`, one row per session (`id`, `created_at`, `data` JSON blob). Replaces the old single flat-file (`chat_sessions.json`) that got fully rewritten on every save — a legacy JSON file is auto-migrated into the DB once on first read if found.
