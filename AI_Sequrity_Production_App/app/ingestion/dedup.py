"""Chunk deduplication engine based on xxhash and SHA256 checksums."""

import hashlib


def compute_chunk_hash(text: str) -> str:
    """Compute a deterministic content hash for chunk deduplication."""
    normalized = " ".join(text.lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def deduplicate_chunks(chunks: list[dict]) -> tuple[list[dict], int]:
    """Deduplicate a list of chunk dicts containing 'text' keys."""
    seen_hashes = set()
    unique_chunks = []
    duplicates_removed = 0

    for chunk in chunks:
        ch_hash = compute_chunk_hash(chunk.get("text", ""))
        if ch_hash in seen_hashes:
            duplicates_removed += 1
            continue
        seen_hashes.add(ch_hash)
        unique_chunks.append(chunk)

    return unique_chunks, duplicates_removed
