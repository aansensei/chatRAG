## infrastructure/database

Toàn bộ database infrastructure. Hiện tại dùng PostgreSQL qua Supabase. Alembic quản lý schema migrations.

### Subdirectories

`migrations/` - Alembic migration scripts, tạo bằng `alembic revision --autogenerate`

`postgres/` - SQLAlchemy engine, session, ORM models, và repository implementations
