# app/core/logging_middleware.py
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

logger = logging.getLogger("app.request")

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()

        # Lấy IP client (ưu tiên x-forwarded-for khi deploy trên Fly/Proxy)
        client_ip = request.headers.get("x-forwarded-for")
        if client_ip:
            client_ip = client_ip.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        method = request.method
        path = request.url.path

        try:
            response = await call_next(request)
        except Exception as exc:
            duration = (time.time() - start) * 1000
            logger.exception(
                f"[ERROR] {method} {path} from {client_ip} - {duration:.2f}ms: {exc}"
            )
            raise

        duration = (time.time() - start) * 1000

        logger.info(
            f"[REQ] {method} {path} from {client_ip} "
            f"-> {response.status_code} in {duration:.2f}ms"
        )

        return response
