# application

Use case layer. Only `retrieval/` has working code today.

| Folder | Status |
|---|---|
| `retrieval/` | **Active** — `ask_question.stream_ask` is the RAG pipeline |
| `auth/` | Empty — login / JWT planned |
| `ingestion/` | Empty — pipeline orchestration logic lives in `workers/` today |
| `jobs/` | Empty — job status logic lives in `infrastructure/queue/redis/publisher.py` |
| `permission/` | Empty — ACL planned for multi-user mode |
| `review/` | Empty — human-review workflow planned |

See `retrieval/README.md` for the only currently implemented use case.
