"""Rate limiting middleware for API."""
import time
from typing import Dict, Tuple
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import structlog

logger = structlog.get_logger()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using token bucket algorithm."""
    
    def __init__(
        self,
        app,
        calls: int = 100,
        period: int = 60,
        identifier: str = "ip"
    ):
        """
        Initialize rate limiter.
        
        Args:
            app: FastAPI application
            calls: Number of calls allowed per period
            period: Time period in seconds
            identifier: How to identify clients ("ip" or "user")
        """
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.identifier = identifier
        self.clients: Dict[str, Tuple[int, float]] = defaultdict(lambda: (calls, time.time()))
        self.cleanup_interval = 300  # Cleanup every 5 minutes
        self.last_cleanup = time.time()
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request."""
        if self.identifier == "ip":
            return request.client.host if request.client else "unknown"
        elif self.identifier == "user":
            # Try to get user from authorization header
            auth_header = request.headers.get("authorization", "")
            if auth_header:
                return auth_header
            return request.client.host if request.client else "unknown"
        return "unknown"
    
    def _cleanup_old_entries(self):
        """Remove old entries to prevent memory leak."""
        current_time = time.time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            expired_keys = [
                key for key, (_, timestamp) in self.clients.items()
                if current_time - timestamp > self.period * 2
            ]
            for key in expired_keys:
                del self.clients[key]
            self.last_cleanup = current_time
            logger.debug("Rate limit cleanup", removed=len(expired_keys))
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with rate limiting."""
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        client_id = self._get_client_id(request)
        current_time = time.time()
        
        # Get or create client bucket
        tokens, last_update = self.clients[client_id]
        
        # Refill tokens based on time elapsed
        time_elapsed = current_time - last_update
        tokens_to_add = (time_elapsed / self.period) * self.calls
        tokens = min(self.calls, tokens + tokens_to_add)
        
        # Check if request can be processed
        if tokens >= 1:
            tokens -= 1
            self.clients[client_id] = (tokens, current_time)
            
            # Add rate limit headers
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(self.calls)
            response.headers["X-RateLimit-Remaining"] = str(int(tokens))
            response.headers["X-RateLimit-Reset"] = str(int(current_time + self.period))
            
            # Periodic cleanup
            self._cleanup_old_entries()
            
            return response
        else:
            # Rate limit exceeded
            retry_after = int(self.period - time_elapsed)
            logger.warning(
                "Rate limit exceeded",
                client_id=client_id,
                path=request.url.path,
                retry_after=retry_after
            )
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.calls),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(current_time + retry_after))
                }
            )


class EndpointRateLimiter:
    """Per-endpoint rate limiter."""
    
    def __init__(self, calls: int = 10, period: int = 60):
        """
        Initialize endpoint rate limiter.
        
        Args:
            calls: Number of calls allowed per period
            period: Time period in seconds
        """
        self.calls = calls
        self.period = period
        self.clients: Dict[str, Dict[str, Tuple[int, float]]] = defaultdict(
            lambda: defaultdict(lambda: (calls, time.time()))
        )
    
    async def __call__(self, request: Request) -> bool:
        """Check rate limit for request."""
        client_id = request.client.host if request.client else "unknown"
        endpoint = f"{request.method}:{request.url.path}"
        current_time = time.time()
        
        # Get or create client bucket for this endpoint
        tokens, last_update = self.clients[client_id][endpoint]
        
        # Refill tokens based on time elapsed
        time_elapsed = current_time - last_update
        tokens_to_add = (time_elapsed / self.period) * self.calls
        tokens = min(self.calls, tokens + tokens_to_add)
        
        # Check if request can be processed
        if tokens >= 1:
            tokens -= 1
            self.clients[client_id][endpoint] = (tokens, current_time)
            return True
        else:
            retry_after = int(self.period - time_elapsed)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for this endpoint. Try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )
