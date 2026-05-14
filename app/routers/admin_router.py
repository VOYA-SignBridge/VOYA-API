from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db 
from app.repositories.publish_repo import PublishRepository
from app.services.admin_service import VideoUploadService
from app.services.publish_service import PublishService
from app.core.exceptions import DataNotFoundError, CloudinaryUploadError, DatabaseOperationalError
from app.schemas.api_response import PageResponse
from app.schemas.sign_video_schema import VideoAdminFlatSchema
from fastapi_pagination.ext.sqlalchemy import paginate
from app.core.config import settings
router = APIRouter(prefix="/admin", tags=["ADMIN SERVICE"])

@router.post("/upload-video")
async def upload_video_endpoint(
    # Parse Form Data
    word_text: str = Form(...), 
    topics: str = Form(...),
    region: str = Form(...),
    variant_id: str = Form(...),
    version: str = Form("v1"),
    file: UploadFile = File(...),
    
    db: Session = Depends(get_db)
):
    service = VideoUploadService(db)
    
    result = await service.process_upload(
        word_text=word_text,
        topics=topics,
        region=region,
        variant=variant_id,
        version=version,
        file=file
    )

    return {
        "code": 200,
        "message": "Upload successful",
        "data": result
    }


@router.get("/videos", response_model=PageResponse[VideoAdminFlatSchema])
def get_videos_endpoint(db: Session = Depends(get_db)):
        service = VideoUploadService(db)
        return service.get_list_videos_formatted()

@router.delete("/videos/{video_id}")
def delete_video_endpoint(video_id: int, db: Session = Depends(get_db)):
    service = VideoUploadService(db)
    return service.delete_video_logic(video_id)


@router.post("/publish/{region}", status_code=status.HTTP_200_OK)
def publish_dictionary_endpoint(region: str, db: Session = Depends(get_db)):
    """
    Trigger build file JSON từ điển và upload lên CDN.
    """
    service = PublishService(db)
    
    try:
        result = service.execute_publish(region)
        return result

    except DataNotFoundError as e:
        # 404: Không có dữ liệu để build
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=str(e)
        )

    except CloudinaryUploadError as e:
        # 502: Lỗi do bên thứ 3 (Bad Gateway)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, 
            detail=str(e)
        )

    except DatabaseOperationalError as e:
        # 503: DB đang chết
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Database connection failed"
        )
        
    except Exception as e:
        # 500: Lỗi không xác định (Bug code)
        print(f"🔥 Critical Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Internal Server Error"
        )
@router.get("/check-version/{region}")
def check_dictionary_version(region: str, db: Session = Depends(get_db)):
    repo = PublishRepository(db)
        
        # Lấy version từ DB (Rất nhẹ, truy vấn mất 1 mili-giây)
    latest_version = repo.get_app_version(region)
        
        # URL file JSON mặc định trên Cloudinary
        # (Đừng quên thay 'dnwwlugjr' bằng cloud name của bạn)
    download_url = f"https://res.cloudinary.com/{settings.cloudinary_cloud_name}/raw/upload/v1/app_config/dictionary_{region}.json"

    return {
        "region": region,
        "latest_version": latest_version,
        "download_url": download_url
    }