import cloudinary
import cloudinary.uploader
import cloudinary.api
from app.core.config import settings
cloudinary.config(
    clould_name= settings.cloudinary_cloud_name,

    api_key=settings.cloudinary_api_key,
    api_secret= settings.cloudinary_api_secret 

)