## shared

Cross-cutting utilities shared across all layers. No business logic here. Does not import from `application`, `domain`, or `infrastructure`.

### Subdirectories

`config/` - app settings loaded from .env

`exceptions/` - custom exception classes

`logger/` - structured logging setup

`security/` - JWT and password hashing

`utils/` - general-purpose utilities
