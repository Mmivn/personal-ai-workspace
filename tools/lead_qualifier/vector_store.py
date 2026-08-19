"""Persist Family Secret knowledge embeddings in a local Qdrant database."""

import argparse
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from qdrant_client import QdrantClient, models

from tools.lead_qualifier.knowledge_base import KnowledgeChunk, load_knowledge_chunks
from tools.lead_qualifier.semantic_search import EmbeddingClient, embedding_client_from_env

COLLECTION_NAME = "family_secret_knowledge"
VECTOR_DB_PATH = Path(__file__).with_name(".qdrant")


@dataclass(frozen=True)
class VectorSearchResult:
    heading: str
    content: str
    source_file: str
    metadata: dict[str, str]
    score: float


def _searchable_text(chunk: KnowledgeChunk) -> str:
    return f"{chunk.heading}\n{chunk.content}"


def _point_id(chunk: KnowledgeChunk) -> str:
    identity = f"{chunk.source_file}\n{chunk.heading}\n{chunk.content}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, identity))


def index_chunks(
    chunks: Sequence[KnowledgeChunk],
    embedding_client: EmbeddingClient,
    qdrant: QdrantClient,
    collection_name: str = COLLECTION_NAME,
) -> int:
    """Create a fresh collection and store each chunk with its embedding."""
    if not chunks:
        return 0

    vectors = embedding_client.embed([_searchable_text(chunk) for chunk in chunks])
    if len(vectors) != len(chunks) or not vectors[0]:
        raise ValueError("Embedding provider returned invalid vectors")

    if qdrant.collection_exists(collection_name):
        qdrant.delete_collection(collection_name)
    qdrant.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=len(vectors[0]),
            distance=models.Distance.COSINE,
        ),
    )
    qdrant.upsert(
        collection_name=collection_name,
        points=[
            models.PointStruct(
                id=_point_id(chunk),
                vector=vector,
                payload={
                    "heading": chunk.heading,
                    "content": chunk.content,
                    "source_file": chunk.source_file,
                    "metadata": chunk.metadata,
                },
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ],
        wait=True,
    )
    return len(chunks)


def search_vector_store(
    query: str,
    embedding_client: EmbeddingClient,
    qdrant: QdrantClient,
    limit: int = 3,
    collection_name: str = COLLECTION_NAME,
) -> list[VectorSearchResult]:
    """Embed only the query and retrieve the nearest stored chunks."""
    if not query.strip() or limit <= 0:
        return []

    query_vectors = embedding_client.embed([query])
    if len(query_vectors) != 1:
        raise ValueError("Embedding provider must return one query vector")

    points = qdrant.query_points(
        collection_name=collection_name,
        query=query_vectors[0],
        with_payload=True,
        limit=limit,
    ).points
    results: list[VectorSearchResult] = []
    for point in points:
        payload = point.payload or {}
        metadata = payload.get("metadata", {})
        results.append(
            VectorSearchResult(
                heading=str(payload.get("heading", "")),
                content=str(payload.get("content", "")),
                source_file=str(payload.get("source_file", "")),
                metadata={str(key): str(value) for key, value in metadata.items()},
                score=point.score,
            )
        )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage the Family Secret vector database")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("index", help="Create embeddings and store all knowledge chunks")
    search_parser = subparsers.add_parser("search", help="Search stored vectors")
    search_parser.add_argument("query", help="Guest question")
    search_parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()

    load_dotenv()
    embedding_client = embedding_client_from_env()
    qdrant = QdrantClient(path=str(VECTOR_DB_PATH))

    if args.command == "index":
        count = index_chunks(load_knowledge_chunks(), embedding_client, qdrant)
        print(f"Indexed {count} Family Secret knowledge chunks.")
        return

    for result in search_vector_store(args.query, embedding_client, qdrant, args.limit):
        print(f"[{result.score:.3f}] {result.heading} ({result.source_file})")
        print(result.content)
        print()


if __name__ == "__main__":
    main()

