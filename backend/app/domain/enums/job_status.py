from enum import Enum


# (str, Enum) để serialize thành string trong JSON, không phải int
class IngestJobStatus(str, Enum):
    PENDING = "pending"
    EXTRACTING = "extracting"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    INDEXING = "indexing"
    COMPLETED = "completed"
    # FAILED có thể xảy ra ở bất kỳ bước nào, retry từ bước bị fail chứ không từ đầu
    FAILED = "failed"


class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
