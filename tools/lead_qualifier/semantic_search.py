"""Semantic search over the Family Secret knowledge base."""

import argparse
import math
import os
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

import requests
from dotenv import load_dotenv

from tools.lead_qualifier.knowledge_base import KnowledgeChunk, load_knowledge_chunks

EMBEDDINGS_URL = "https://api.openai.com/v1/embeddings"
DEFAULT_MODEL = "text-embedding-3-small"
GEMINI_EMBEDDINGS_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-embedding-001:batchEmbedContents"
)
DEFAULT_GEMINI_MODEL = "gemini-embedding-001"


@dataclass(frozen=True)
class SearchResult:
    chunk: KnowledgeChunk
    score: float


class EmbeddingClient(Protocol):
    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class GeminiEmbeddingClient:
    """Gemini embedding client used by default for its available free tier."""

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_GEMINI_MODEL,
        timeout: float = 30.0,
        session: requests.Session | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.session = session or requests.Session()

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []

        model_name = f"models/{self.model}"
        response = self.session.post(
            GEMINI_EMBEDDINGS_URL,
            headers={
                "x-goog-api-key": self.api_key,
                "Content-Type": "application/json",
            },
            json={
                "requests": [
                    {
                        "model": model_name,
                        "content": {"parts": [{"text": text}]},
                        "taskType": "SEMANTIC_SIMILARITY",
                        "outputDimensionality": 768,
                    }
                    for text in texts
                ]
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return [item["values"] for item in response.json()["embeddings"]]


class OpenAIEmbeddingClient:
    """Small REST client so the search code does not depend on an SDK."""

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        timeout: float = 30.0,
        session: requests.Session | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.session = session or requests.Session()

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []

        response = self.session.post(
            EMBEDDINGS_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={"model": self.model, "input": list(texts)},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        ordered_items = sorted(payload["data"], key=lambda item: item["index"])
        return [item["embedding"] for item in ordered_items]


def _cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Embedding vectors must have the same dimensions")

    dot_product = sum(a * b for a, b in zip(left, right, strict=True))
    left_length = math.sqrt(sum(value * value for value in left))
    right_length = math.sqrt(sum(value * value for value in right))
    if left_length == 0 or right_length == 0:
        return 0.0
    return dot_product / (left_length * right_length)


def search_chunks(
    query: str,
    chunks: Sequence[KnowledgeChunk],
    client: EmbeddingClient,
    limit: int = 3,
) -> list[SearchResult]:
    """Return chunks ordered by semantic similarity to the query."""
    if not query.strip() or not chunks or limit <= 0:
        return []

    searchable_texts = [f"{chunk.heading}\n{chunk.content}" for chunk in chunks]
    embeddings = client.embed([query, *searchable_texts])
    if len(embeddings) != len(searchable_texts) + 1:
        raise ValueError("Embedding API returned an unexpected number of vectors")

    query_embedding = embeddings[0]
    results = [
        SearchResult(chunk=chunk, score=_cosine_similarity(query_embedding, embedding))
        for chunk, embedding in zip(chunks, embeddings[1:], strict=True)
    ]
    return sorted(results, key=lambda result: result.score, reverse=True)[:limit]


def embedding_client_from_env() -> EmbeddingClient:
    """Build the configured embedding provider, preferring Gemini's free tier."""
    provider = os.getenv("EMBEDDING_PROVIDER", "gemini").lower()
    if provider == "openai":
        return OpenAIEmbeddingClient(os.getenv("OPENAI_API_KEY", ""))
    if provider == "gemini":
        return GeminiEmbeddingClient(os.getenv("GEMINI_API_KEY", ""))
    raise ValueError("EMBEDDING_PROVIDER must be 'gemini' or 'openai'")


def main() -> None:
    parser = argparse.ArgumentParser(description="Search the Family Secret knowledge base")
    parser.add_argument("query", help="Guest question")
    parser.add_argument("--limit", type=int, default=3, help="Number of chunks to return")
    args = parser.parse_args()

    load_dotenv()
    client = embedding_client_from_env()
    for result in search_chunks(args.query, load_knowledge_chunks(), client, args.limit):
        print(f"[{result.score:.3f}] {result.chunk.heading} ({result.chunk.source_file})")
        print(result.chunk.content)
        print()


if __name__ == "__main__":
    main()
