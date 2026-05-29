## presentation/api/documents

Document management routes. This is the first endpoint group to be implemented.

Planned: `POST /documents/upload` receives a file, saves it to storage, creates a Document entity, and triggers an IngestJob. `GET /documents/` lists documents. `DELETE /documents/{id}`.
