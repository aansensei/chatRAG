## presentation

HTTP layer. FastAPI routers, middleware, and WebSocket handlers. The only layer that handles HTTP concerns (status codes, request parsing, response serialization).

This layer calls use cases from the application layer and never imports from infrastructure directly. No business logic here.

### Subdirectories

`api/` - REST API routers grouped by resource

`middleware/` - request middleware (auth, permission, rate limiting)

`websocket/` - WebSocket handlers
