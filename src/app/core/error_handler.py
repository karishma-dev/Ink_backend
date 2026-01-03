from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import AppException
from app.schemas.error import ErrorResponse
from app.core.logger import logger

async def exception_handler(request: Request, exc: AppException):
    logger.error(f"Exception: {exc.code} - {exc.message}")

    error_response = ErrorResponse(
        status="error",
        message=exc.message,
        code=exc.code,
        details=exc.details
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump()
    )

