from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from app.routers import auth_router, room_router, room_ws_router
from app.db.database import engine, Base
from app.core import exceptions
from app.core.auth_middleware import AuthMiddleware
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)
app = FastAPI(title="VOYA SignBridge Backend")

app.include_router(room_ws_router.router)

app.include_router(auth_router.router)
app.include_router(room_router.router)
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

@app.get("/")
def root():
    return {"message": "Welcome to VOYA SignBridge Backend"}