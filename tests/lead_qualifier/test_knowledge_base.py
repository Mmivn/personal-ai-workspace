from pathlib import Path

from tools.lead_qualifier.knowledge_base import chunk_markdown, load_knowledge_chunks


def test_loads_family_secret_knowledge_documents():
    chunks = load_knowledge_chunks()

    assert chunks
    assert {chunk.source_file for chunk in chunks} == {
        "menu_overview.md",
        "reservations.md",
        "restaurant_info.md",
    }
    assert any(chunk.heading == "Opening hours" for chunk in chunks)
    assert any("09:00–23:00" in chunk.content for chunk in chunks)


def test_chunk_keeps_source_metadata(tmp_path: Path):
    document = tmp_path / "example.md"
    document.write_text(
        """---
source: https://example.com
venue: Family Secret
---

# Contact

Phone: 0354 057 942.

## Hours

Daily.
""",
        encoding="utf-8",
    )

    chunks = chunk_markdown(document)

    assert [chunk.heading for chunk in chunks] == ["Contact", "Hours"]
    assert chunks[0].metadata == {
        "source": "https://example.com",
        "venue": "Family Secret",
    }
    assert chunks[0].source_file == "example.md"


def test_empty_sections_do_not_create_empty_chunks(tmp_path: Path):
    document = tmp_path / "empty.md"
    document.write_text("# First\n\n## Second\n\nUseful information.\n", encoding="utf-8")

    chunks = chunk_markdown(document)

    assert len(chunks) == 1
    assert chunks[0].heading == "Second"
    assert chunks[0].content == "Useful information."

