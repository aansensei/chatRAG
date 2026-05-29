## presentation/api/documents

Document management routes. Đây là endpoint đầu tiên sẽ implement.

Sẽ có: `POST /documents/upload` nhận file, lưu storage, tạo Document entity, trigger IngestJob. `GET /documents/` list. `DELETE /documents/{id}`.
