from dataclasses import dataclass, field


@dataclass
class ExtractResult:
    text: str = ""
    tables: list[dict] = field(default_factory=list)
    images: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
