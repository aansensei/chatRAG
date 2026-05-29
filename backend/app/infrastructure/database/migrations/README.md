## infrastructure/database/migrations

Alembic migration scripts. Each migration is a forward-only schema change — never edit a migration that has already run, only add new ones.

Apply migrations: `alembic upgrade head`

Generate a new migration: `alembic revision --autogenerate -m "short description"`

Roll back one step: `alembic downgrade -1`
