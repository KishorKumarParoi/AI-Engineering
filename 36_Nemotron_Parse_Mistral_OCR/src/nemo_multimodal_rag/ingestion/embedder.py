"""Phase 4: Embed text chunks using NVIDIA NIM nv-embedqa-e5-v5."""

from __future__ import annotations

import logging

from openai import AsyncOpenAI

from nemo_multimodal_rag.config import Settings

log = logging.getLogger(__name__)

# Maximum texts per API call to avoid payload limits
_DEFAULT_BATCH_SIZE = 32


async def embed_chunks(
    texts: list[str],
    client: AsyncOpenAI,
    settings: Settings,
    input_type: str = "passage",
    batch_size: int = _DEFAULT_BATCH_SIZE,
) -> list[list[float]]:
    """Embed a list of text strings using the NIM embedding model.

    The NIM ``nv-embedqa-e5-v5`` model requires an ``input_type`` to
    distinguish between passage (document) and query embedding spaces.

    Args:
        texts: List of strings to embed.
        client: AsyncOpenAI NIM client.
        settings: Pipeline settings (provides model name and dimensions).
        input_type: ``"passage"`` for documents, ``"query"`` for search queries.
        batch_size: Number of texts per API call (default 32).

    Returns:
        List of embedding vectors in the same order as ``texts``.
    """
    if not texts:
        return []

    all_embeddings: list[list[float]] = []

    for batch_start in range(0, len(texts), batch_size):
        batch = texts[batch_start : batch_start + batch_size]

        # Replace empty strings with a placeholder so the API doesn't reject them
        safe_batch = [t if t.strip() else "[empty]" for t in batch]

        response = await client.embeddings.create(
            model=settings.nvidia_embed_model,
            input=safe_batch,
            extra_body={
                "input_type": input_type,
                "truncate": "END",
            },
        )

        batch_embeddings = [item.embedding for item in response.data]
        all_embeddings.extend(batch_embeddings)

        log.debug(
            "Embedded batch %d-%d (%s)",
            batch_start,
            batch_start + len(batch) - 1,
            input_type,
        )

    log.info("Embedded %d texts as %s vectors.", len(all_embeddings), input_type)
    return all_embeddings
