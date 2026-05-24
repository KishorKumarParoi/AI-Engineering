from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import logging

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    '''Middleware to add a unique request ID to each incoming request for better traceability.'''
    
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        logger.info(f"Request ID {request_id} - {request.method} {request.url}")

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        logger.info(f"Request Completed - Request ID {request_id} - Status Code: {response.status_code}")

        return response