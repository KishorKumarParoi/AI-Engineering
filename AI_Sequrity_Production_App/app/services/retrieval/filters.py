"""Qdrant metadata filter builders for targeted document retrieval."""

from qdrant_client.models import Filter, FieldCondition, MatchValue


def build_source_filter(source_tag: str | None = None) -> Filter | None:
    """Construct a Qdrant filter based on source category (e.g. 'true', 'noisy')."""
    if not source_tag:
        return None
    return Filter(
        must=[
            FieldCondition(
                key="metadata.source",
                match=MatchValue(value=source_tag)
            )
        ]
    )
