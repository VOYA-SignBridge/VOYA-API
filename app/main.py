from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from app.core.logging_middleware import LoggingMiddleware
from app.core.rate_limite_middleware import RateLimitMiddleware
from app.db.data_initializer import init_seed_data
from app.routers import auth_router, room_router, room_ws_router, sign_video_router, ai_router
from app.db.database import engine, Base, get_db
from app.core import exceptions
# from app.core.auth_middleware import AuthMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.utils.sign_cache import sign_cache
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import HTMLResponse

# from app.ai.embedding_text import build_sign_embeddings

Base.metadata.create_all(bind=engine)
app = FastAPI(title="VOYA SignBridge Backend")
api_prefix = APIRouter(prefix="/api/v1")

api_prefix.include_router(room_ws_router.router)
api_prefix.include_router(auth_router.router)
api_prefix.include_router(room_router.router)
api_prefix.include_router(sign_video_router.router)
api_prefix.include_router(ai_router.router)
app.include_router(api_prefix)
#--dang ly exception handlers--
app.add_exception_handler(HTTPException, exceptions.http_exception_handler)
app.add_exception_handler(RequestValidationError, exceptions.validation_exception_handler)
app.add_exception_handler(ValidationError, exceptions.validation_exception_handler)
app.add_exception_handler(Exception, exceptions.global_exception_handler)
app.add_exception_handler(StarletteHTTPException, exceptions.http_exception_handler)
#app.add_middleware(AuthMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.on_event("startup")
def startup_event():
    db = next(get_db())

    init_seed_data(db)
    # build_sign_embeddings(db)
    sign_cache.reload(db)   # chỉ chạy 1 lần khi app start
    db.close()
    print("Sign cache loaded")

@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <html>
        <head>
            <title>VOYA SignBridge Backend</title>
            <style>
                body { font-family: Arial; padding: 32px; background: #fafafa; }
                .box { 
                    max-width: 600px; margin: auto; padding: 24px; 
                    background: white; border-radius: 16px; 
                    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                }
                h1 { color: #4B7BEC; }
                p { color: #555; font-size: 16px; }
                a { color: #20bf6b; font-weight: bold; text-decoration: none; }
            </style>
        </head>
        <body>
            <div class="box">
                <h1>VOYA SignBridge Backend</h1>
                <p>Your backend is running successfully </p>

                <p>Explore API docs:</p>
                <ul>
                    <li><a href="/docs">Swagger UI</a></li>
                    <li><a href="/redoc">ReDoc UI</a></li>
                </ul>

                <p>Current status: <b style="color:green;">ONLINE</b></p>
            </div>
        </body>
    </html>
    """

