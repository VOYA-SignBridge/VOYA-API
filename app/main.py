from fastapi import Depends, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from app.core.dependencies import get_current_user
from app.db.data_initializer import init_seed_data
from app.routers import auth_router, room_router, room_ws_router, sign_video_router
from app.db.database import engine, Base, get_db
from app.core import exceptions
from app.core.auth_middleware import AuthMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.utils.sign_cache import sign_cache
from app.utils.init_db import init_db
from cloudinary.utils import cloudinary_url


Base.metadata.create_all(bind=engine)
app = FastAPI(title="VOYA SignBridge Backend")
app.include_router(room_ws_router.router)

app.include_router(auth_router.router)
app.include_router(room_router.router)
app.include_router(sign_video_router.router)

# app.include_router(ai_router.router)
#--dang ly exception handlers--
app.add_exception_handler(Exception, exceptions.global_exception_handler)
app.add_exception_handler(HTTPException, exceptions.http_exception_handler)
app.add_exception_handler(ValidationError, exceptions.validation_exception_handler)

app.add_middleware(AuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.on_event("startup")
def startup_event():
    db = next(get_db())

    init_seed_data(db)

    sign_cache.reload(db)   # chỉ chạy 1 lần khi app start
    db.close()
    print("Sign cache loaded")
@app.get("/")
def root():
    return {"message": "Welcome to VOYA SignBridge Backend"}
@app.get("/test-cloudinary")
def test_cloudinary(meL: dict = Depends(get_current_user)):
    url, _ = cloudinary_url(
        "voya_sign_language/chao_y9ra17",  # public_id của video chào
        resource_type="video",
        secure=True,
    )
    return {"url": url}