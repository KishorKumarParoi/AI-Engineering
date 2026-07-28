import pytest
from app.services.cache_service import (
    clear_query_cache,
    get_cache_key,
    get_cached_response,
    normalize_query,
    set_cached_response,
)


def test_normalize_query():
    assert normalize_query("  What is Kubernetes Pod?  ") == "what is kubernetes pod"
    assert normalize_query("WHAT IS KUBERNETES POD???") == "what is kubernetes pod"
    assert normalize_query("hello world!") == "hello world"


def test_get_cache_key_consistency():
    key1 = get_cache_key("What is a pod?")
    key2 = get_cache_key("  what is a pod?  ")
    key3 = get_cache_key("WHAT IS A POD???")
    assert key1 == key2 == key3


def test_cache_set_and_get():
    query = "test query for caching"
    data = {
        "question": query,
        "answer": "A test answer.",
        "thought_process": ["Step 1", "Step 2"],
        "status": "Response generated.",
        "sources": [],
    }

    # Clear before testing
    clear_query_cache()

    # Set cache
    success = set_cached_response(query, data, ttl_seconds=60)
    if success:
        cached = get_cached_response(query)
        assert cached is not None
        assert cached["answer"] == "A test answer."
        assert cached["question"] == query

        # Test case-insensitive normalization retrieval
        cached_case = get_cached_response("  TEST QUERY FOR CACHING??? ")
        assert cached_case is not None
        assert cached_case["answer"] == "A test answer."

        # Clean up
        clear_query_cache()
