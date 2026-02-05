# schemas.py
import datetime
from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class TranslateRequest(BaseModel):
    text: str

class SignVideo(BaseModel):
    sign_id: int
    key: str
    phrase: str
    mp4_url: str
    webm_url: str


class TranslateResponse(BaseModel):
    text: str
    videos: List[SignVideo]



class VideoAdminFlatSchema(BaseModel):
    id: int
    word: str
    slug: str
    region: str
    topic: Optional[str] = None
    variant: str  
    version: str
    public_id: str
    preview_url: str
    format: Optional[str] = "mp4" 
    created_at: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

# class WordAdminResponseSchema(BaseModel):
#     id: int
#     word: str
#     slug: str
#     region: str
#     topics: List[str]
#     # Lồng danh sách video của từ đó vào đây
#     videos: List[VideoAdminFlatSchema] 

#     model_config = ConfigDict(from_attributes=True)