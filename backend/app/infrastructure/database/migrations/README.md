## infrastructure/database/migrations

Alembic migration scripts. Mỗi migration là một bước thay đổi schema không thể đảo ngược - không sửa migration đã chạy, chỉ thêm migration mới.

Chạy migration: `alembic upgrade head`

Tạo migration mới: `alembic revision --autogenerate -m "mô tả ngắn"`

Rollback 1 bước: `alembic downgrade -1`
