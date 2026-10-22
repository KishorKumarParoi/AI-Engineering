from app.services.retrieval.cache import EmbeddingLRUCache


def test_cache_hit_and_eviction():
    cache = EmbeddingLRUCache(capacity=2)
    cache.set("q1", [0.1, 0.2])
    cache.set("q2", [0.3, 0.4])

    assert cache.get("q1") == [0.1, 0.2]

    # Insert third, should evict least recently used (q2)
    cache.set("q3", [0.5, 0.6])
    assert cache.get("q2") is None
    assert cache.get("q1") == [0.1, 0.2]
    assert cache.get("q3") == [0.5, 0.6]
