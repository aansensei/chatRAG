from dataclasses import dataclass


@dataclass
class ChunkConfig:
    max_tokens: int = 500
    overlap_tokens: int = 50
