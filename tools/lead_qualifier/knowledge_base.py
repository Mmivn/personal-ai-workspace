"""Load Family Secret knowledge documents and split them into searchable chunks."""

from dataclasses import dataclass
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).with_name("knowledge")


@dataclass(frozen=True)
class KnowledgeChunk:
    """One self-contained section of a knowledge document."""

    source_file: str
    heading: str
    content: str
    metadata: dict[str, str]


def _split_front_matter(text: str) -> tuple[dict[str, str], str]:
    """Return simple YAML-style metadata and the remaining Markdown body."""
    if not text.startswith("---\n"):
        return {}, text

    closing_marker = text.find("\n---\n", 4)
    if closing_marker == -1:
        return {}, text

    metadata: dict[str, str] = {}
    for line in text[4:closing_marker].splitlines():
        key, separator, value = line.partition(":")
        if separator and key.strip() and value.strip():
            metadata[key.strip()] = value.strip()

    return metadata, text[closing_marker + 5 :]


def chunk_markdown(path: Path) -> list[KnowledgeChunk]:
    """Split a Markdown document at headings while preserving useful context."""
    metadata, body = _split_front_matter(path.read_text(encoding="utf-8"))
    chunks: list[KnowledgeChunk] = []
    current_heading = path.stem.replace("_", " ").title()
    current_lines: list[str] = []

    def save_chunk() -> None:
        content = "\n".join(current_lines).strip()
        if content:
            chunks.append(
                KnowledgeChunk(
                    source_file=path.name,
                    heading=current_heading,
                    content=content,
                    metadata=metadata.copy(),
                )
            )

    for line in body.splitlines():
        if line.startswith("#"):
            save_chunk()
            current_lines = []
            current_heading = line.lstrip("#").strip()
        else:
            current_lines.append(line)

    save_chunk()
    return chunks


def load_knowledge_chunks(directory: Path = KNOWLEDGE_DIR) -> list[KnowledgeChunk]:
    """Load every Markdown knowledge document in deterministic order."""
    chunks: list[KnowledgeChunk] = []
    for path in sorted(directory.glob("*.md")):
        chunks.extend(chunk_markdown(path))
    return chunks

