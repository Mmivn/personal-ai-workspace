from unittest.mock import Mock

import pytest

from tools.lead_qualifier.knowledge_base import KnowledgeChunk
from tools.lead_qualifier.semantic_search import (
    GEMINI_EMBEDDINGS_URL,
    GeminiEmbeddingClient,
    OpenAIEmbeddingClient,
    _cosine_similarity,
    search_chunks,
)


def _chunk(heading: str) -> KnowledgeChunk:
    return KnowledgeChunk(
        source_file="test.md",
        heading=heading,
        content=f"Information about {heading}",
        metadata={"venue": "Family Secret"},
    )


def test_search_orders_chunks_by_semantic_similarity():
    client = Mock()
    client.embed.return_value = [
        [1.0, 0.0],  # query
        [0.0, 1.0],  # address
        [0.9, 0.1],  # opening hours
        [0.5, 0.5],  # menu
    ]

    results = search_chunks(
        "When are you open?",
        [_chunk("Address"), _chunk("Opening hours"), _chunk("Menu")],
        client,
        limit=2,
    )

    assert [result.chunk.heading for result in results] == ["Opening hours", "Menu"]
    client.embed.assert_called_once()


def test_embedding_client_preserves_api_result_order():
    response = Mock()
    response.json.return_value = {
        "data": [
            {"index": 1, "embedding": [0.0, 1.0]},
            {"index": 0, "embedding": [1.0, 0.0]},
        ]
    }
    session = Mock()
    session.post.return_value = response
    client = OpenAIEmbeddingClient("test-key", session=session)

    embeddings = client.embed(["first", "second"])

    assert embeddings == [[1.0, 0.0], [0.0, 1.0]]
    response.raise_for_status.assert_called_once()


def test_gemini_embedding_client_uses_batch_api():
    response = Mock()
    response.json.return_value = {
        "embeddings": [
            {"values": [1.0, 0.0]},
            {"values": [0.0, 1.0]},
        ]
    }
    session = Mock()
    session.post.return_value = response
    client = GeminiEmbeddingClient("test-key", session=session)

    embeddings = client.embed(["first", "second"])

    assert embeddings == [[1.0, 0.0], [0.0, 1.0]]
    _, kwargs = session.post.call_args
    assert session.post.call_args.args[0] == GEMINI_EMBEDDINGS_URL
    assert kwargs["headers"]["x-goog-api-key"] == "test-key"
    assert len(kwargs["json"]["requests"]) == 2
    assert kwargs["json"]["requests"][0]["taskType"] == "SEMANTIC_SIMILARITY"
    response.raise_for_status.assert_called_once()


def test_cosine_similarity_rejects_different_dimensions():
    with pytest.raises(ValueError, match="same dimensions"):
        _cosine_similarity([1.0], [1.0, 0.0])


def test_blank_query_returns_no_results():
    client = Mock()

    assert search_chunks("   ", [_chunk("Menu")], client) == []
    client.embed.assert_not_called()
