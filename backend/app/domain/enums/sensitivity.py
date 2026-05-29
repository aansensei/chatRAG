from enum import Enum


# thứ tự tăng dần theo độ nhạy cảm: PUBLIC < INTERNAL < CONFIDENTIAL < SECRET
class SensitivityLevel(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    # CONFIDENTIAL trở lên bắt buộc phải qua human review trước khi deploy vào search index
    CONFIDENTIAL = "confidential"
    SECRET = "secret"


class DocumentStatus(str, Enum):
    PROCESSING = "processing"
    # READY là trạng thái duy nhất để document xuất hiện trong kết quả search
    READY = "ready"
    FAILED = "failed"
    ARCHIVED = "archived"


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    # VIEWER chỉ read, không upload, không edit
    VIEWER = "viewer"
