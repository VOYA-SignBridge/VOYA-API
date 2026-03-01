import redis.asyncio as redis
from dotenv import load_dotenv
import os
from app.core.config import settings
load_dotenv()


redis_client = redis.from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True
)