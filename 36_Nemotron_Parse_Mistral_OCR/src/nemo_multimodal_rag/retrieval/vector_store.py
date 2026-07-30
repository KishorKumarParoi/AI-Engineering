"""Phase 5: Qdrant vector indexing and retrieval."""

from __future__ import annotations

import logging
from typing import Any

from qdrant_client import AsyncQdrantClient, models
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    HnswConfigDiff,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)

from nemo_multimodal_rag.config import Settings
from nemo_multimodal_rag.ingestion.chunker import Chunk

log = logging.getLogger(__name__)

_BATCH_SIZE = 100


async def get_qdrant_client(settings: Settings) -> AsyncQdrantClient:
    """Create and return an AsyncQdrantClient."""
    return AsyncQdrantClient(url=settings.qdrant_url)


async def ensure_collection(client: AsyncQdrantClient, settings: Settings) -> None:
    """Create the Qdrant collection if it does not already exist.

    Uses a dense-only HNSW index with cosine distance at ``embed_dim`` dimensions.
    Payload indexes are created for ``chunk_type``, ``page_num``, and
    ``section_header`` to support filtered retrieval.

    Args:
        client: AsyncQdrantClient instance.
        settings: Pipeline settings.
    """
    collection_name = settings.qdrant_collection_name

    existing = await client.get_collections()
    existing_names = {c.name for c in existing.collections}

    if collection_name in existing_names:
        log.info("Collection '%s' already exists — skipping creation.", collection_name)
        return

    await client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=settings.embed_dim,
            distance=Distance.COSINE,
            hnsw_config=HnswConfigDiff(m=16, ef_construct=100),
        ),
    )
    log.info("Created collection '%s' (dim=%d, cosine).", collection_name, settings.embed_dim)

    # Payload indexes for efficient filtered search
    for field_name, schema_type in [
        ("chunk_type", PayloadSchemaType.KEYWORD),
        ("page_num", PayloadSchemaType.INTEGER),
        ("section_header", PayloadSchemaType.KEYWORD),
    ]:
        await client.create_payload_index(
            collection_name=collection_name,
            field_name=field_name,
            field_schema=schema_type,
        )
        log.debug("Created payload index on '%s'.", field_name)


async def upsert_chunks(
    chunks: list[Chunk],
    embeddings: list[list[float]],
    client: AsyncQdrantClient,
    settings: Settings,
) -> None:
    """Upsert chunk embeddings and payloads to Qdrant in batches of 100.

    Args:
        chunks: Chunk objects (metadata source).
        embeddings: Embedding vectors in the same order as ``chunks``.
        client: AsyncQdrantClient instance.
        settings: Pipeline settings.
    """
    if len(chunks) != len(embeddings):
        raise ValueError(
            f"Mismatch: {len(chunks)} chunks vs {len(embeddings)} embeddings"
        )

    collection_name = settings.qdrant_collection_name
    points: list[PointStruct] = []

    for i, (chunk, vector) in enumerate(zip(chunks, embeddings)):
        # Build original_caption from any Caption source elements
        original_caption = " ".join(
            e.text
            for e in chunk.source_elements
            if e.element_type == "Caption" and e.text.strip()
        )

        payload: dict[str, Any] = {
            "chunk_id": chunk.chunk_id,
            "chunk_type": chunk.chunk_type,
            "text": chunk.text,
            "original_caption": original_caption,
            "page_num": chunk.page_num,
            "bbox": chunk.bbox,
            "section_header": chunk.section_header,
            "doc_title": chunk.doc_title,
            "source_element_types": [e.element_type for e in chunk.source_elements],
        }

        points.append(
            PointStruct(id=i, vector=vector, payload=payload)
        )

    # Batch upsert
    for batch_start in range(0, len(points), _BATCH_SIZE):
        batch = points[batch_start : batch_start + _BATCH_SIZE]
        await client.upsert(collection_name=collection_name, points=batch)
        log.debug("Upserted points %d-%d.", batch_start, batch_start + len(batch) - 1)

    log.info("Upserted %d points to '%s'.", len(points), collection_name)


async def retrieve_chunks(
    query_vector: list[float],
    client: AsyncQdrantClient,
    settings: Settings,
    top_k: int = 5,
    chunk_type_filter: str | None = None,
) -> list[dict[str, Any]]:
    """Query the vector store and return the top-k matching chunk payloads.

    Bibliography chunks are excluded by default unless explicitly requested.

    Args:
        query_vector: Embedded query vector.
        client: AsyncQdrantClient instance.
        settings: Pipeline settings.
        top_k: Number of results to return.
        chunk_type_filter: If set, filter to only this chunk_type.

    Returns:
        List of payload dicts for the top-k results, ordered by relevance.
    """
    collection_name = settings.qdrant_collection_name

    if chunk_type_filter:
        query_filter = Filter(
            must=[FieldCondition(key="chunk_type", match=MatchValue(value=chunk_type_filter))]
        )
    else:
        # Exclude bibliography by default (not useful for Q&A)
        query_filter = Filter(
            must_not=[
                FieldCondition(key="chunk_type", match=MatchValue(value="bibliography"))
            ]
        )

    results = await client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=top_k,
        with_payload=True,
        query_filter=query_filter,
    )

    payloads = []
    for scored_point in results.points:
        payload = dict(scored_point.payload or {})
        payload["_score"] = scored_point.score
        payloads.append(payload)

    return payloads
