
from fastapi import APIRouter
from fastapi.params import Depends
from app.core.dependencies import get_current_user
from app.services.sign_video_service import text_to_sign_videos
from app.schemas.sign_video_schema import TranslateRequest, TranslateResponse

router = APIRouter(prefix="/sign_video", tags=["Sign Video"])

@router.post("/translate", response_model=TranslateResponse )
def translate_text_to_sign_videos(request: TranslateRequest):
    videos = text_to_sign_videos(request.text)
    return TranslateResponse(text=request.text, videos=videos)
