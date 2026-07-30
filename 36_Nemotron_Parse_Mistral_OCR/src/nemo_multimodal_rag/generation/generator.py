"""Phase 6: RAG answer generation using NVIDIA NIM LLM."""

from __future__ import annotations

import logging
from typing import Any

from openai import AsyncOpenAI

from nemo_multimodal_rag.config import Settings
from nemo_multimodal_rag.ingestion.embedder import embed_chunks
from nemo_multimodal_rag.retrieval.vector_store import retrieve_chunks

log = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a helpful technical assistant. Answer the user's question using ONLY "
    "the provided context passages. If the context does not contain enough information "
    "to answer the question, say so clearly. Do not make up information."
)


async def retrieve_and_answer(
    query: str,
    client: AsyncOpenAI,
    qdrant_client: Any,
    settings: Settings,
    top_k: int = 5,
    chunk_type_filter: str | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    """Embed a query, retrieve relevant chunks, and generate a grounded answer.

    Args:
        query: User's natural language question.
        client: AsyncOpenAI NIM client (shared for embedding + generation).
        qdrant_client: AsyncQdrantClient instance.
        settings: Pipeline settings.
        top_k: Number of context chunks to retrieve.
        chunk_type_filter: Optional filter — e.g. ``"table"``, ``"image"``.

    Returns:
        Tuple of (answer_string, list_of_retrieved_chunk_payloads).
    """
    # Embed the query with input_type="query"
    query_vectors = await embed_chunks(
        texts=[query],
        client=client,
        settings=settings,
        input_type="query",
    )
    query_vector = query_vectors[0]

    # Retrieve top-k chunks
    context_chunks = await retrieve_chunks(
        query_vector=query_vector,
        client=qdrant_client,
        settings=settings,
        top_k=top_k,
        chunk_type_filter=chunk_type_filter,
    )

    if not context_chunks:
        return "No relevant content found in the knowledge base.", []

    # Generate answer
    answer = await generate_answer(query, context_chunks, client, settings)
    return answer, context_chunks


async def generate_answer(
    query: str,
    context_chunks: list[dict[str, Any]],
    client: AsyncOpenAI,
    settings: Settings,
) -> str:
    """Generate a grounded answer from the retrieved context.

    Args:
        query: User's question.
        context_chunks: Retrieved chunk payloads from the vector store.
        client: AsyncOpenAI NIM client.
        settings: Pipeline settings.

    Returns:
        Generated answer string.
    """
    # Build context block
    context_parts = []
    for i, chunk in enumerate(context_chunks, 1):
        chunk_type = chunk.get("chunk_type", "text")
        page = chunk.get("page_num", "?")
        section = chunk.get("section_header", "")
        text = chunk.get("text", "").strip()

        header = f"[{i}] (page {page}"
        if section:
            header += f", section: {section}"
        header += f", type: {chunk_type})"

        context_parts.append(f"{header}\n{text}")

    context_str = "\n\n---\n\n".join(context_parts)

    user_message = f"Context:\n\n{context_str}\n\n---\n\nQuestion: {query}"

    response = await client.chat.completions.create(
        model=settings.nvidia_llm_model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.0,
        max_tokens=1024,
    )

    answer = response.choices[0].message.content or ""
    log.debug("Generated answer (%d chars) from %d context chunks.", len(answer), len(context_chunks))
    return answer
