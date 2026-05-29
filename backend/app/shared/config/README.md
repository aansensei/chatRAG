## shared/config

App configuration. Uses Pydantic Settings to load and validate environment variables from `.env`.

Planned: `settings.py` with a `Settings(BaseSettings)` class containing DB URL, Qdrant host, embedding model path, JWT secret, storage backend, and queue backend. Import from here wherever config is needed.
