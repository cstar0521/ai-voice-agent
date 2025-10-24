"""
Rate limiting middleware for API protection.
Implements per-IP and per-endpoint rate limiting with Redis backend.
"""

import time
from typing import Dict, Optional, Callable
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio

from app.logging_config import get_logger

logger = get_logger('security')


class InMemoryRateLimiter:
    """
    In-memory rate limiter using sliding window algorithm.
    For production, use Redis-based rate limiter.
    """
    
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = asyncio.Lock()
    
    async def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, Dict]:
        """
        Check if request is allowed based on rate limit.
        
        Args:
            key: Unique identifier (IP address, user ID, etc.)
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        async with self.lock:
            now = time.time()
            cutoff = now - window_seconds
            
            # Remove old requests outside the window
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if req_time > cutoff
            ]
            
            current_count = len(self.requests[key])
            
            # Check if limit exceeded
            if current_count >= max_requests:
                oldest_request = min(self.requests[key])
                retry_after = int(oldest_request + window_seconds - now)
                
                return False, {
                    "limit": max_requests,
                    "remaining": 0,
                    "reset": int(oldest_request + window_seconds),
                    "retry_after": retry_after
                }
            
            # Add current request
            self.requests[key].append(now)
            
            return True, {
                "limit": max_requests,
                "remaining": max_requests - current_count - 1,
                "reset": int(now + window_seconds)
            }
    
    async def cleanup_old_entries(self):
        """Periodic cleanup of old entries to prevent memory leak."""
        async with self.lock:
            now = time.time()
            keys_to_delete = []
            
            for key, timestamps in self.requests.items():
                # Remove entries older than 1 hour
                self.requests[key] = [
                    ts for ts in timestamps
                    if now - ts < 3600
                ]
                
                # Mark empty entries for deletion
                if not self.requests[key]:
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del self.requests[key]


# Global rate limiter instance
rate_limiter = InMemoryRateLimiter()


class RateLimitMiddleware:
    """
    Rate limiting middleware for FastAPI.
    """
    
    def __init__(
        self,
        default_limit: int = 100,
        default_window: int = 60,
        webhook_limit: int = 1000,
        webhook_window: int = 60
    ):
        """
        Initialize rate limit middleware.
        
        Args:
            default_limit: Default requests per window (100 req/min)
            default_window: Default window in seconds (60s)
            webhook_limit: Webhook requests per window (1000 req/min)
            webhook_window: Webhook window in seconds (60s)
        """
        self.default_limit = default_limit
        self.default_window = default_window
        self.webhook_limit = webhook_limit
        self.webhook_window = webhook_window
        
        # Endpoint-specific limits
        self.endpoint_limits = {
            "/api/v1/calls/inbound/webhook": (webhook_limit, webhook_window),
            "/api/v1/calls/outbound/webhook": (webhook_limit, webhook_window),
        }
    
    async def __call__(self, request: Request, call_next: Callable):
        """Process request with rate limiting."""
        
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Get rate limit for endpoint
        path = request.url.path
        max_requests, window_seconds = self.endpoint_limits.get(
            path,
            (self.default_limit, self.default_window)
        )
        
        # Create rate limit key
        rate_limit_key = f"{client_ip}:{path}"
        
        # Check rate limit
        is_allowed, rate_info = await rate_limiter.is_allowed(
            rate_limit_key,
            max_requests,
            window_seconds
        )
        
        # Add rate limit headers
        headers = {
            "X-RateLimit-Limit": str(rate_info["limit"]),
            "X-RateLimit-Remaining": str(rate_info["remaining"]),
            "X-RateLimit-Reset": str(rate_info["reset"]),
        }
        
        if not is_allowed:
            # Rate limit exceeded
            headers["Retry-After"] = str(rate_info["retry_after"])
            
            logger.warning(
                f"Rate limit exceeded",
                extra={
                    "client_ip": client_ip,
                    "path": path,
                    "limit": max_requests,
                    "window": window_seconds
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Please try again in {rate_info['retry_after']} seconds.",
                    "retry_after": rate_info["retry_after"]
                },
                headers=headers
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        for key, value in headers.items():
            response.headers[key] = value
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address from request.
        Handles X-Forwarded-For header for proxied requests.
        """
        # Check X-Forwarded-For header (for proxied requests)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        if request.client:
            return request.client.host
        
        return "unknown"


def add_security_headers(response):
    """Add security headers to response for DDoS protection."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response


# Decorator for endpoint-specific rate limiting
def rate_limit(max_requests: int, window_seconds: int = 60):
    """
    Decorator for endpoint-specific rate limiting.
    
    Args:
        max_requests: Maximum requests allowed
        window_seconds: Time window in seconds
        
    Example:
        @router.post("/expensive-operation")
        @rate_limit(max_requests=10, window_seconds=60)
        async def expensive_operation():
            pass
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get request from kwargs
            request = kwargs.get('request') or (args[0] if args else None)
            
            if not isinstance(request, Request):
                # If no request object, skip rate limiting
                return await func(*args, **kwargs)
            
            # Get client IP
            client_ip = request.client.host if request.client else "unknown"
            rate_limit_key = f"{client_ip}:{func.__name__}"
            
            # Check rate limit
            is_allowed, rate_info = await rate_limiter.is_allowed(
                rate_limit_key,
                max_requests,
                window_seconds
            )
            
            if not is_allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Retry after {rate_info['retry_after']} seconds.",
                    headers={"Retry-After": str(rate_info["retry_after"])}
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# Background task to cleanup old rate limit entries
async def cleanup_rate_limiter():
    """Background task to periodically cleanup old rate limit entries."""
    while True:
        await asyncio.sleep(300)  # Run every 5 minutes
        await rate_limiter.cleanup_old_entries()
        logger.debug("Rate limiter cleanup completed")
