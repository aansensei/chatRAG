# chatRAG

Enterprise Retrieval Augmented Generation Platform developed during internship at SADEC Technology Joint Stock Company.

chatRAG enables organizations to upload, classify, and query internal documents through a role-aware AI chat interface. The system enforces access control at the retrieval layer, ensuring users only receive answers derived from documents their role is authorized to access.

---

## Repository Structure

```
chatRAG/
    backend/        FastAPI backend, ingestion pipeline, RAG engine
    frontend/       React admin and chat interface (in development)
```

Each subdirectory contains its own README with layer-specific setup instructions and architecture notes.

---

## System Overview

```
User (React Frontend)
        |
        | HTTP / WebSocket
        v
API Gateway (FastAPI)
        |
        |-- Retrieval --> Vector Search --> Access Control Filter --> Rerank --> LLM --> Stream response
        |
        |-- Ingestion --> OCR --> Chunk --> AI Classify --> Human Review --> Embed --> Vector DB
```

---

## Tech Stack

**Backend**
* FastAPI for the API gateway and WebSocket streaming
* PostgreSQL for relational metadata, job state, and access control rules
* Qdrant for vector similarity search and metadata-filtered retrieval
* Redis and Celery for the asynchronous event-driven ingestion pipeline
* PaddleOCR for optical character recognition on scanned documents
* Unstructured for structure-aware document parsing and chunking

**Frontend**
* React for the admin dashboard and chat interface
* Vite as the development and build toolchain

**Infrastructure**
* Docker and Docker Compose for containerized local and production deployment
* MinIO for S3-compatible document storage in production
* Prometheus and Grafana for metrics and operational monitoring

---

## Quick Start

### Prerequisites

* Python 3.11 or higher
* Node.js 18 or higher
* Docker and Docker Compose
* PostgreSQL with the pgvector extension installed
* Redis

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

API available at `http://localhost:8000`
API docs available at `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Admin interface available at `http://localhost:5173`

### Full Stack with Docker

```bash
docker-compose -f backend/docker/docker-compose.yml up --build
```

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in the values before starting any service.

| Variable | Description | Required |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `REDIS_URL` | Redis connection string | Yes |
| `QDRANT_HOST` | Qdrant hostname | Yes |
| `QDRANT_PORT` | Qdrant port | Yes |
| `OPENAI_API_KEY` | OpenAI API key for cloud models | No |
| `LLM_PROVIDER` | `openai`, `groq`, or `ollama` | Yes |
| `STORAGE_BACKEND` | `local` or `minio` | Yes |
| `RETRIEVAL_TOP_K` | Candidate chunks before rerank (default 15) | No |
| `RERANK_TOP_K` | Final chunks passed to LLM (default 8) | No |

---

## Deployment

### Local Development

Run backend and frontend individually as described in Quick Start above.

### Staging and Production

All components are containerized. Update the following before deploying to a live environment.

* Set `STORAGE_BACKEND=minio` and configure MinIO credentials
* Add production domain origins to the CORS allowed list in `backend/app/shared/config`
* Replace the default secret key in `backend/.env.prod`
* Optionally migrate from Redis to Kafka by swapping the queue provider in infrastructure config

A `docker-compose.yml` for full-stack production deployment is located at `backend/docker/docker-compose.yml`.

---

## Documentation

* Backend architecture and pipeline details: `backend/README.md`
* Frontend component structure: `frontend/README.md` (coming soon)

---

## Project Status

| Component | Status |
|---|---|
| Backend scaffold and architecture | Complete |
| Domain layer and event definitions | Complete |
| Ingestion pipeline workers | In development |
| Retrieval and reranking service | In development |
| React frontend | Planned |
| Docker production setup | Planned |
