from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette import status
import logging
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
logger = logging.getLogger("uvicorn.error")

class AppError(Exception):
    """Base class cho lỗi của ứng dụng"""
    pass

class DataNotFoundError(AppError):
    """Lỗi khi không tìm thấy dữ liệu trong DB"""
    pass

class CloudinaryUploadError(AppError):
    """Lỗi khi upload thất bại"""
    pass

class DatabaseOperationalError(AppError):
    """Lỗi kết nối DB"""
    pass
# --- HTTPException: lỗi nghiệp vụ / auth / 4xx rõ ràng ---
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(
        f"[HTTP {exc.status_code}] {exc.detail} - Path: {request.url.path}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": exc.status_code,
            "error": exc.__class__.__name__,
            "message": exc.detail,
            "path": str(request.url.path),
        },
    )

# --- Validation: dữ liệu request sai ---
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"[422 Validation] {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": 422,
            "error": "ValidationError",
            "message": "Invalid input data",
            "details": exc.errors(),
            "path": str(request.url.path),
        },
    )

# --- Global: bug hệ thống thật sự (500) ---
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, (FastAPIHTTPException, StarletteHTTPException)):
        logger.warning(
            f"[HTTP {exc.status_code}] {getattr(exc, 'detail', str(exc))} - Path: {request.url.path}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": exc.status_code,
                "error": exc.__class__.__name__,
                "message": getattr(exc, "detail", str(exc)),
                "path": str(request.url.path),
            },
        )

    # Các lỗi 500 thật sự
    logger.exception(f"[500] Unhandled error at {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": 500,
            "error": "InternalServerError",
            "message": "Internal server error",
            "path": str(request.url.path),
        },
    )
