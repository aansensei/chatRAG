## shared

Cross-cutting utilities dùng chung giữa tất cả layers. Không có business logic ở đây. Không import từ `application`, `domain`, hay `infrastructure`.

### Subdirectories

`config/` - app settings load từ .env

`exceptions/` - custom exception classes

`logger/` - structured logging setup

`security/` - JWT, password hashing

`utils/` - general-purpose utilities
