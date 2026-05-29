## shared/config

App configuration. Dùng Pydantic Settings để load và validate environment variables từ `.env`.

Sẽ có: `settings.py` với class `Settings(BaseSettings)` chứa DB URL, Qdrant host, embedding model path, JWT secret, storage backend, queue backend. Import ở bất kỳ đâu cần config.
