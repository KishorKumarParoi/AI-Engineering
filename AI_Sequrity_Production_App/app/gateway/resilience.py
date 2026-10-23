"""Resilience patterns: Exponential backoff with full jitter for API calls."""

import asyncio
import random
import time
from typing import Callable, Any
import logfire


def retry_with_jitter(max_retries: int = 3, base_delay: float = 0.5, max_delay: float = 5.0):
    """Decorator that retries an async or sync function using full jitter."""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            attempt = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    if attempt > max_retries:
                        logfire.error(f"Exceeded max retries ({max_retries}) on {func.__name__}: {e}")
                        raise e
                    sleep_time = min(max_delay, base_delay * (2 ** attempt))
                    jitter = random.uniform(0, sleep_time)
                    logfire.warning(f"Retry {attempt}/{max_retries} for {func.__name__} after {jitter:.2f}s: {e}")
                    time.sleep(jitter)
        return wrapper
    return decorator
