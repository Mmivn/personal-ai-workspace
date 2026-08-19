from collections.abc import Sequence

from qdrant_client import QdrantClient

from tools.lead_qualifier.knowledge_base import KnowledgeChunk
from tools.lead_qualifier.vector_store import index_chunks, search_vector_store


class FakeEmbeddingClient:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        vectors = []
        for text in texts:
            normalized = text.lower()
            if "hour" in normalized or "open" in normalized:
                vectors.append([1.0, 0.0])
            elif "child" in normalized or "kid" in normalized:
                vectors.append([0.0, 1.0])
            else:
                vectors.append([0.5, 0.5])
        return vectors


def _chunk(heading: str, content: str) -> KnowledgeChunk:
    return KnowledgeChunk(
        source_file="restaurant_info.md",
        heading=heading,
        content=content,
        metadata={"venue": "Family Secret"},
    )


def test_indexes_chunks_and_searches_with_only_the_query_embedding():
    qdrant = QdrantClient(":memory:")
    embedding_client = FakeEmbeddingClient()
    chunks = [
        _chunk("Opening hours", "Open daily from 09:00 to 23:00."),
        _chunk("Children", "A children's play area is available."),
    ]

    assert index_chunks(chunks, embedding_client, qdrant) == 2
    results = search_vector_store("When are you open?", embedding_client, qdrant, limit=1)

    assert results[0].heading == "Opening hours"
    assert results[0].metadata == {"venue": "Family Secret"}
    assert len(embedding_client.calls[0]) == 2
    assert embedding_client.calls[1] == ["When are you open?"]


def test_reindex_replaces_old_collection_contents():
    qdrant = QdrantClient(":memory:")
    embedding_client = FakeEmbeddingClient()

    index_chunks([_chunk("Old", "Other information")], embedding_client, qdrant)
    index_chunks([_chunk("Children", "A children's play area")], embedding_client, qdrant)
    results = search_vector_store("kids", embedding_client, qdrant, limit=5)

    assert [result.heading for result in results] == ["Children"]


def test_blank_query_does_not_call_embedding_provider():
    embedding_client = FakeEmbeddingClient()

    assert search_vector_store(" ", embedding_client, QdrantClient(":memory:")) == []
    assert embedding_client.calls == []

