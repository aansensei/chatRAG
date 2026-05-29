## tests

Test suite. Chạy toàn bộ: `pytest tests/`

### Subdirectories

`unit/` - pure unit tests, không có I/O. Test domain entities, enum logic, utility functions. Không cần DB hay Docker. Chạy nhanh.

`integration/` - test với real services (PostgreSQL, Qdrant, Redis). Yêu cầu docker-compose đang chạy. Verify các repository implementations thực sự hoạt động với DB thật.

`e2e/` - end-to-end tests qua HTTP API. Upload document → poll job → query → verify response. Test toàn bộ pipeline từ đầu đến cuối.
