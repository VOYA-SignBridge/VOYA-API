# app/services/sign_video_service.py
from app.utils.sign_cache import sign_cache
from app.utils.normalize_text import normalize
from cloudinary.utils import cloudinary_url
from app.schemas.sign_video_schema import SignVideo

def text_to_sign_videos(text: str) -> list[SignVideo]:
    norm = normalize(text)
    if not norm:
        return []

    tokens = norm.split()
    matched = sign_cache.match_tokens(tokens)

    videos: list[SignVideo] = []

    for item in matched:
        url, _ = cloudinary_url(
            item["public_id"],
            resource_type="video",
            secure=True,
            format="mp4"
        )
        videos.append(
            SignVideo(
                sign_id=item["sign_id"],
                key=item["key"],
                phrase=item["phrase_raw"],
                url=url,
            )
        )

    return videos
