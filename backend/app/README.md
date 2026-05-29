## app

Root của Python application. Theo Clean Architecture với 4 layer chính:

```
domain       - business rules thuần, không có dependency ngoài
application  - use cases, chỉ phụ thuộc vào domain
infrastructure - implementations, có thể import bất kỳ thư viện nào
presentation - HTTP/WebSocket layer, nhận request và gọi use cases
```

Import chỉ được đi từ ngoài vào trong. `presentation` import `application`, `application` import `domain`, không bao giờ ngược lại. `infrastructure` implement interfaces của `domain`, không được import từ `application`.

`shared` là ngoại lệ - cross-cutting utilities, mọi layer đều có thể dùng.

### Files

`__init__.py` - entry point, hiện tại trống.
