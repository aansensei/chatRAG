## infrastructure/database/postgres

SQLAlchemy implementation for PostgreSQL.

### Files

`connection.py` - creates the AsyncEngine and async session factory. Import this as a FastAPI dependency in routes that need a DB session.

### Subdirectories

`models/` - SQLAlchemy ORM models (map to DB tables), distinct from domain entities

`repositories/` - concrete implementations of the repository interfaces from domain
