
# from fastapi import Request
# from starlette.middleware.base import BaseHTTPMiddleware
# PUBLIC_PATHS = {
#     "/docs",
#     "/redoc",
#     "/openapi.json",
#     "/"
# }

# class AuthMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#         path = request.url.path
#         request.state.user = None

#         if request.method == "OPTIONS":
#             return await call_next(request)

#         if (
#             path in PUBLIC_PATHS
#             or path.startswith("/static")
#             or path.startswith("/ws/")
#             or path.startswith("/api/v1/ws/")
#             or path.startswith("/api/v1/auth/me")   # login/signup không cần token
#         ):
#             return await call_next(request)
