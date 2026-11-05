from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ReferenceDoc:
    source: str
    text: str


def load_reference(knowledge_dir: Path) -> list[ReferenceDoc]:
    return [
        ReferenceDoc(file.name, file.read_text(encoding="utf-8").strip())
        for file in sorted(knowledge_dir.glob("*.md"))
    ]


def format_reference(docs: list[ReferenceDoc]) -> str:
    return "\n\n---\n\n".join(f"[source: {d.source}]\n{d.text}" for d in docs)
