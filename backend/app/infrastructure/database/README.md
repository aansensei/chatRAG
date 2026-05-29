## infrastructure/database

All database infrastructure. Currently using PostgreSQL via Supabase. Alembic manages schema migrations.

### Subdirectories

`migrations/` - Alembic migration scripts, generated with `alembic revision --autogenerate`

`postgres/` - SQLAlchemy engine, session factory, ORM models, and repository implementations
