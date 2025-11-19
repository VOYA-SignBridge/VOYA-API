# schemas.py
from pydantic import BaseModel
from typing import List

class TranslateRequest(BaseModel):
    text: str

class SignVideo(BaseModel):
    sign_id: int
    key: str
    phrase: str
    url: str

class TranslateResponse(BaseModel):
    text: str
    videos: List[SignVideo]
