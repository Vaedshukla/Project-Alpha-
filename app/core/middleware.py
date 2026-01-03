from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from time import time
from collections import defaultdict
from typing import Dict

from app.utils.responses import error


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware."""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Clean old entries (older than 1 minute)
        now = time()
        self.requests[client_ip] = [
            ts for ts in self.requests[client_ip]
            if now - ts < 60
        ]
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content=error("Rate limit exceeded. Please try again later.", None)
            )
        
        # Record request
        self.requests[client_ip].append(now)
        
        response = await call_next(request)
        return response


def sanitize_input(text: str) -> str:
    """Basic input sanitization to prevent injection attacks."""
    if not text:
        return ""
    # Remove null bytes
    text = text.replace("\x00", "")
    # Truncate excessively long inputs
    if len(text) > 10000:
        text = text[:10000]
    return text

