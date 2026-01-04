from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.exceptions import AppException, RateLimitException
from app.schemas.error import ErrorResponse
from app.core.logger import logger
import traceback

async def app_exception_handler(request: Request, exc: AppException):
    """Handle all AppException subclasses"""
    logger.error(f"AppException: {exc.code} - {exc.message}")
    
    error_response = ErrorResponse(
        status="error",
        message=exc.message,
        code=exc.code,
        details=exc.details
    )
    
    response = JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump()
    )
    
    # Add Retry-After header for rate limit errors
    if isinstance(exc, RateLimitException):
        response.headers["Retry-After"] = str(exc.retry_after)
    
    return response

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    logger.warning(f"Validation error: {exc.errors()}")
    
    error_response = ErrorResponse(
        status="error",
        message="Invalid request data",
        code="VALIDATION_ERROR",
        details={"errors": exc.errors()}
    )
    
    return JSONResponse(
        status_code=422,
        content=error_response.model_dump()
    )

async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors gracefully"""
    logger.error(f"Unhandled exception: {str(exc)}\n{traceback.format_exc()}")
    
    error_response = ErrorResponse(
        status="error",
        message="An unexpected error occurred. Please try again later.",
        code="INTERNAL_ERROR",
        details=None  # Don't expose internal details to client
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump()
    )

# Legacy alias for backward compatibility
exception_handler = app_exception_handler
