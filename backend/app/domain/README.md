## domain

Core business layer. No imports from infrastructure, no I/O, no HTTP. The only part of the codebase that can be tested completely without a database or network connection.

Everything else depends on this layer; this layer depends on nothing outside stdlib and pydantic.

### Subdirectories

`entities/` - business objects (Document, Chunk, User, ...)

`enums/` - shared enums used across entities

`events/` - domain events signaling that something happened

`repositories/` - abstract interfaces for data access, implemented in infrastructure
