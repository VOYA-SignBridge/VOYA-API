import cloudinary.uploader
from fastapi import UploadFile, HTTPException
from fastapi_pagination import paginate
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from slugify import slugify
from app.core.config import settings
from app.models.sign_video import WordVideo, DictionaryWord
from app.repositories.sign_video_repo import VideoRepository

class VideoUploadService:
    def __init__(self, db: Session):
        self.repo = VideoRepository(db)

    def _generate_public_id(self, region: str, slug: str, version: str, variant: str) -> str:
        return f"sign_language/{region}/{slug}/{version}/{variant}/video"
    async def process_upload(self, word_text: str, topics: str, region: str, variant: str, version: str, file: UploadFile):
        # 1. Slugify & Generate ID (Giữ nguyên)
        word_slug = slugify(word_text, separator="_")
        region_slug = slugify(region, separator="_")
        variant_slug = slugify(variant, separator="_")
        final_public_id = self._generate_public_id(region_slug, word_slug, version, variant_slug)
        ui_folder_path = f"sign_language/{region_slug}/{word_slug}/{version}/{variant_slug}"
        print(f"Generated UI FOLDER: {ui_folder_path}")
        try:
                
                
            # 2. Upload Cloudinary (Giữ nguyên)
            print(f"🚀 Uploading to Cloudinary: {final_public_id}")
            upload_result = cloudinary.uploader.upload(
                file.file,
                resource_type="video",
                public_id=final_public_id,
                overwrite=True,
                invalidate=True,
                asset_folder=ui_folder_path,
                eager=[{"format": "mp4", "quality": "auto", "width": 720, "crop": "limit"}]
            )
            
            # 3. Thao tác DB (Repository chỉ flush, chưa commit)
            word_obj = self.repo.get_or_create_word(
                word_text=word_text, 
                slug=word_slug, 
                region=region_slug, 
                topics=topics
            )

            # Lấy ID của word_obj để dùng (vẫn an toàn vì session chưa đóng)
            self.repo.upsert_video_metadata(
                word_id=word_obj.id,
                variant=variant_slug,
                version=version,
                public_id=final_public_id,
                cloud_ver=upload_result.get("version")
            )

            # 4. CHỐT SỔ (COMMIT TRANSACTION) TẠI ĐÂY
            # Lúc này mọi data mới thực sự được ghi cứng vào DB
            self.repo.commit_changes()

            return {
                "word": word_text,
                "variant": variant_slug,
                "cdn_url": upload_result.get("secure_url"),
                "cloud_path": final_public_id
            }

        except Exception as e:
            # Nếu có lỗi, session tự rollback khi request kết thúc
            print(f"Error: {e}")
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    

    def get_list_videos_formatted(self):
        """
        Business Logic: Lấy dữ liệu DB -> Biến đổi thành JSON chuẩn cho Frontend
        """
        raw_videos = self.repo.get_all_videos_with_details()
        
        # Transform: Chuyển object SQLAlchemy thành List Dict
        result = []
        for v in raw_videos:
            # Xử lý an toàn nếu word_rel bị null (dù hiếm)
            word_info = v.word_rel
            
            result.append({
                "id": v.id,
                "word": word_info.word if word_info else "Unknown",
                "slug": word_info.slug if word_info else "",
                "region": word_info.region if word_info else "",
                "topic": word_info.topics if word_info else [], # Trả về mảng topic
                "variant": v.variant_id,
                "version": v.version_str,
                "public_id": v.public_id,
                "preview_url": f"https://res.cloudinary.com/{settings.cloudinary_cloud_name}/video/upload/v{v.cloud_version}/{v.public_id}.mp4"
            })
            
        return result


    def get_admin_words_service(db: Session):
        # Sử dụng joinedload để gộp 2 bảng DictionaryWord và WordVideo vào 1 query duy nhất
        query = (
            select(DictionaryWord)
            .options(joinedload(DictionaryWord.videos))
            .order_by(DictionaryWord.id.desc())
        )
        
        # paginate sẽ tự động xử lý trả về Page[WordAdminResponseSchema]
        return paginate(db, query)
    def delete_video_logic(self, video_id: int):
        """
        Business Logic: Xóa trên Cloudinary trước -> Xóa DB sau
        """
        # 1. Tìm video
        video = self.repo.get_video_by_id(video_id)
        if not video:
            raise HTTPException(status_code=404, detail="Video không tồn tại")

        try:
            # 2. Xóa trên Cloudinary
            print(f"🗑 Delete Cloudinary: {video.public_id}")
            cloudinary.uploader.destroy(video.public_id, resource_type="video")

            # 3. Xóa trong DB
            self.repo.delete_video(video)
            self.repo.commit_changes() # Chốt sổ
            
            return {"status": "success", "message": "Đã xóa video thành công"}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lỗi xóa video: {str(e)}")