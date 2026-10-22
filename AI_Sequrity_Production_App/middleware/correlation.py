"""FastAPI Correlation ID middleware for end-to-end distributed request tracing."""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import logfire


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        corr_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request.state.correlation_id = corr_id
        with logfire.span("HTTP Request", correlation_id=corr_id, path=request.url.path):
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = corr_id
            return response
