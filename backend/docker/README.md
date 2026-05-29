## docker

Docker configuration for the full stack.

### Files

`Dockerfile.api` - image for the FastAPI server. Multi-stage build: install deps → copy code → expose port 8000.

`Dockerfile.worker` - image for worker processes. Same base as the API image but with a different entrypoint — runs a worker script instead of uvicorn.

`docker-compose.yml` - full local dev stack: API, workers, PostgreSQL, Qdrant, Redis/Kafka. Mounts code as a volume for hot-reload during development.
