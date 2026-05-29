## infrastructure/database/postgres

SQLAlchemy implementation cho PostgreSQL.

### Files

`connection.py` - tạo AsyncEngine và async session factory. Import ở đây để dùng làm dependency trong FastAPI routes.

### Subdirectories

`models/` - SQLAlchemy ORM models (map DB tables), khác với domain entities

`repositories/` - concrete implementations của repository interfaces từ domain
