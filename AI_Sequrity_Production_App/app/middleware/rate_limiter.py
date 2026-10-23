"""In-memory Token Bucket rate limiter per IP address."""

import time
from collections import defaultdict
from fastapi import HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class TokenBucketLimiter:
    def __init__(self, rate_per_second: float = 10.0, burst: int = 30):
        self.rate = rate_per_second
        self.burst = burst
        self.tokens = defaultdict(lambda: burst)
        self.last_check = defaultdict(time.time)

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        elapsed = now - self.last_check[client_ip]
        self.last_check[client_ip] = now
        self.tokens[client_ip] = min(self.burst, self.tokens[client_ip] + elapsed * self.rate)
        if self.tokens[client_ip] >= 1.0:
            self.tokens[client_ip] -= 1.0
            return True
        return False
