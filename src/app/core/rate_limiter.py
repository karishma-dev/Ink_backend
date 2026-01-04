"""
Rate Limiting Middleware using SlowAPI

This module provides rate limiting for API endpoints using SlowAPI (slowapi).
Rate limits are configurable per endpoint and per user.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
from app.schemas.error import ErrorResponse
from app.core.logger import logger

def get_user_identifier(request: Request) -> str:
    """
    Get unique identifier for rate limiting.
    Uses user_id from auth header if available, otherwise falls back to IP.
    """
    # Try to get user from authorization header (if already authenticated)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        # Use a hash of the token as identifier (more privacy-preserving)
        return f"user:{hash(auth_header)}"
    
    # Fall back to IP address for unauthenticated requests
    return get_remote_address(request)

# Create limiter instance
limiter = Limiter(key_func=get_user_identifier)

# Rate limit configurations
RATE_LIMITS = {
    "chat": "30/minute",        # 30 chat requests per minute
    "upload": "10/minute",      # 10 uploads per minute
    "default": "100/minute",    # 100 requests per minute for other endpoints
    "auth": "10/minute",        # 10 auth attempts per minute (login/register)
}

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom handler for rate limit exceeded errors"""
    logger.warning(f"Rate limit exceeded for {get_user_identifier(request)}: {exc.detail}")
    
    # Parse retry-after from the exception
    retry_after = 60  # Default
    if hasattr(exc, 'retry_after'):
        retry_after = exc.retry_after
    
    error_response = ErrorResponse(
        status="error",
        message="Rate limit exceeded. Please slow down and try again later.",
        code="RATE_LIMIT_EXCEEDED",
        details={"retry_after": retry_after}
    )
    
    response = JSONResponse(
        status_code=429,
        content=error_response.model_dump()
    )
    response.headers["Retry-After"] = str(retry_after)
    
    return response
