## tests

Test suite. Run all: `pytest tests/`

### Subdirectories

`unit/` - pure unit tests, no I/O. Tests domain entities, enum logic, and utility functions. No DB or Docker required. Fast.

`integration/` - tests against real services (PostgreSQL, Qdrant, Redis). Requires docker-compose to be running. Verifies that repository implementations actually work with a real database.

`e2e/` - end-to-end tests over the HTTP API. Upload a document → poll the job → query → verify the response. Tests the full pipeline from start to finish.
