from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette import status
import logging

# --- Cấu hình logger  ---
logger = logging.getLogger("uvicorn.error")

# --- Bắt lỗi HTTPException  ---
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTPException: {exc.detail} - Path: {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": exc.status_code,
            "error": exc.__class__.__name__,
            "message": exc.detail,
            "path": request.url.path,
        },
    )

# --- Bắt lỗi validation ---
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error at {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": 422,
            "error": "ValidationError",
            "message": "Invalid input data",
            "details": exc.errors(),
        },
    )

# --- Bắt lỗi hệ thống  ---
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error at {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": 500,
            "error": "InternalServerError",
            "message": str(exc),
            "path": request.url.path,
        },
    )
