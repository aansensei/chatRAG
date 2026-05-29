## presentation

HTTP layer. FastAPI routers, middleware, và WebSocket handlers. Layer duy nhất xử lý HTTP concerns (status codes, request parsing, response serialization).

Presentation layer gọi use cases từ application layer, không gọi infrastructure trực tiếp. Không có business logic ở đây.

### Subdirectories

`api/` - REST API routers grouped by resource

`middleware/` - request middleware (auth, permission, rate limit)

`websocket/` - WebSocket handlers
