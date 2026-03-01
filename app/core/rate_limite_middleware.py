# app/core/rate_limit_middleware.py
import time
from typing import Dict, Tuple

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# { ip: (window_start_timestamp, count) }
RATE_LIMIT_STORE: Dict[str, Tuple[float, int]] = {}

MAX_REQUESTS = 60        # Số request tối đa
WINDOW_SECONDS = 60      # Trong bao nhiêu giây
RATE_LIMIT_PUBLIC_PATHS = {
    "/docs",
    "/redoc",
    "/openapi.json",
    "/",
}
RATE_LIMIT_PREFIX_IGNORE = (
    "/static",
    "/ws",
)

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Bỏ qua rate limit cho 1 số path
        if (
            path in RATE_LIMIT_PUBLIC_PATHS
            or path.startswith(RATE_LIMIT_PREFIX_IGNORE)
        ):
            return await call_next(request)

        # Lấy IP
        client_ip = request.headers.get("x-forwarded-for")
        if client_ip:
            client_ip = client_ip.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        now = time.time()
        window_start, count = RATE_LIMIT_STORE.get(client_ip, (now, 0))

        # Nếu còn trong window hiện tại
        if now - window_start < WINDOW_SECONDS:
            if count >= MAX_REQUESTS:
                # Hết quota
                retry_after = int(WINDOW_SECONDS - (now - window_start))

                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "status": 429,
                        "error": "TooManyRequests",
                        "message": "Rate limit exceeded. Try again later.",
                        "retry_after": retry_after,
                    },
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(MAX_REQUESTS),
                        "X-RateLimit-Remaining": "0",
                    },
                )

            # Còn quota → tăng count
            RATE_LIMIT_STORE[client_ip] = (window_start, count + 1)
        else:
            # Hết window cũ → reset
            RATE_LIMIT_STORE[client_ip] = (now, 1)

        response = await call_next(request)

        # Thêm header rate limit (tuỳ thích)
        window_start, count = RATE_LIMIT_STORE.get(client_ip, (now, 1))
        remaining = max(0, MAX_REQUESTS - count)

        response.headers["X-RateLimit-Limit"] = str(MAX_REQUESTS)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response
