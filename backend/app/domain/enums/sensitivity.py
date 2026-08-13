from enum import Enum


# ascending sensitivity order: PUBLIC < INTERNAL < CONFIDENTIAL < SECRET
class SensitivityLevel(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    # CONFIDENTIAL and above require mandatory human review before deploying to the search index
    CONFIDENTIAL = "confidential"
    SECRET = "secret"


class DocumentStatus(str, Enum):
    PROCESSING = "processing"
    # READY is the only status that makes a document appear in search results
    READY = "ready"
    FAILED = "failed"
    ARCHIVED = "archived"


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    # VIEWER can only read — no uploads, no edits
    VIEWER = "viewer"
