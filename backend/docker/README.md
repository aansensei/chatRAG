## docker

Docker configuration cho toàn bộ stack.

### Files

`Dockerfile.api` - image cho FastAPI server. Multi-stage build: install deps → copy code → expose port 8000.

`Dockerfile.worker` - image cho worker processes. Cùng base với api nhưng entrypoint khác - chạy worker script thay vì uvicorn.

`docker-compose.yml` - full local dev stack: API, workers, PostgreSQL, Qdrant, Redis/Kafka. Mount code dưới dạng volume để hot-reload khi dev.
