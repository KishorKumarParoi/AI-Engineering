"""LRU Memory Cache for pre-computed query embeddings."""

from collections import OrderedDict
import threading

class EmbeddingLRUCache:
    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.cache: OrderedDict[str, list[float]] = OrderedDict()
        self.lock = threading.Lock()

    def get(self, query: str) -> list[float] | None:
        with self.lock:
            key = query.strip().lower()
            if key in self.cache:
                self.cache.move_to_end(key)
                return self.cache[key]
            return None

    def set(self, query: str, vector: list[float]) -> None:
        with self.lock:
            key = query.strip().lower()
            self.cache[key] = vector
            self.cache.move_to_end(key)
            if len(self.cache) > self.capacity:
                self.cache.popitem(last=False)

query_embedding_cache = EmbeddingLRUCache(capacity=500)
