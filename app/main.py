from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from app.core.logging_middleware import LoggingMiddleware
from app.core.rate_limite_middleware import RateLimitMiddleware
# from app.db.data_initializer import init_seed_data
from app.routers import auth_router, room_router, room_ws_router, sign_video_router, ai_router, admin_router
from app.db.database import engine, Base, get_db
from app.core import exceptions
# from app.core.auth_middleware import AuthMiddleware
from fastapi.middleware.cors import CORSMiddleware
# from app.utils.sign_cache import sign_cache
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import HTMLResponse
from fastapi_pagination import add_pagination
# from app.ai.embedding_text import build_sign_embeddings

Base.metadata.create_all(bind=engine)
app = FastAPI( 
    title="VOYA SignBridge Backend",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json")
api_prefix = APIRouter(prefix="/api/v1")

api_prefix.include_router(room_ws_router.router)
api_prefix.include_router(auth_router.router)
api_prefix.include_router(room_router.router)
# api_prefix.include_router(sign_video_router.router)
api_prefix.include_router(ai_router.router)
api_prefix.include_router(admin_router.router)
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
# app/main.py

# app/main.py

origins = [
    # 1. Localhost (Dành cho trình duyệt trên máy tính đang code)
    "http://localhost:5173",    # Vite (React) mặc định
    "http://127.0.0.1:5173",   
    "http://localhost:3000",    # React cũ/Create React App
    "http://127.0.0.1:3000",
    "http://localhost:8080",    # Port phổ biến khác

    # 2. Local IP (Quan trọng để test React Native hoặc điện thoại thật)
    "http://192.168.1.2:5173",  
    "http://192.168.1.10:5173", 
    "http://10.0.2.2:8081",     # Android Emulator truy cập về localhost máy tính

    # 3. Domain Production (Khi bạn đã deploy Web Admin lên host)
    "https://se.cit.ctu.edu.vn",
    "https://admin.yourdomain.com",
    "https://ctusignbridge.vercel.app"
    
    # Custom Backend App domains
    "http://api-signbridge.tamdevx.id.vn",
    "https://api-signbridge.tamdevx.id.vn",

    # 4. Mobile Apps (React Native)
    "null", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Dùng danh sách cụ thể
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.on_event("startup")
def startup_event():
    db = next(get_db())

    # init_seed_data(db)
    # build_sign_embeddings(db)
    #sign_cache.reload(db)   
    db.close()

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
                    <li><a href="/api/v1/docs">Swagger UI</a></li>
                    <li><a href="/api/v1/redoc">ReDoc UI</a></li>
                </ul>

                <p>Current status: <b style="color:green;">ONLINE</b></p>
            </div>
        </body>
    </html>
    """

add_pagination(app)