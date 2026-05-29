## domain

Core business layer. Không import gì từ infrastructure, không có I/O, không có HTTP. Đây là phần duy nhất của codebase có thể test hoàn toàn mà không cần DB hoặc network.

Mọi thứ còn lại phụ thuộc vào layer này, layer này không phụ thuộc vào bất cứ thứ gì ngoài stdlib và pydantic.

### Subdirectories

`entities/` - các business objects (Document, Chunk, User, ...)

`enums/` - shared enums dùng chung giữa entities

`events/` - domain events, tín hiệu "đã xảy ra việc X"

`repositories/` - abstract interfaces cho data access, implemented ở infrastructure
