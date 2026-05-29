## app

Root of the Python application. Follows Clean Architecture with four main layers:

```
domain         - pure business rules, no external dependencies
application    - use cases, depends only on domain
infrastructure - concrete implementations, can import any library
presentation   - HTTP/WebSocket layer, receives requests and calls use cases
```

Imports only flow inward. `presentation` imports `application`, `application` imports `domain`, never the other way around. `infrastructure` implements domain interfaces but is never imported by `application`.

`shared` is the exception — cross-cutting utilities that any layer can use.

### Files

`__init__.py` - package entry point, currently empty.
