import json
import time
import cloudinary.uploader
from sqlalchemy.orm import Session

from app.repositories.publish_repo import PublishRepository
from app.core.exceptions import DataNotFoundError, CloudinaryUploadError

class PublishService:
    def __init__(self, db: Session):
        self.repo = PublishRepository(db)

    def execute_publish(self, region: str) -> dict:
        """Hàm main thực thi quy trình publish"""
        
        # 1. Lấy dữ liệu
        words = self.repo.get_words_with_videos_by_region(region)
        
        if not words:
            raise DataNotFoundError(f"Không tìm thấy từ vựng nào cho vùng miền: {region}")

        # 2. Transform dữ liệu (Tách ra hàm riêng cho sạch)
        final_package = self._transform_to_json_structure(region, words)

        # 3. Upload lên Cloudinary
        url = self._upload_json_to_cloud(region, final_package)

        return {
            "status": "success",
            "region": region,
            "total_words": len(words),
            "version": final_package["meta"]["version"],
            "url": url
        }

    def _transform_to_json_structure(self, region: str, words: list) -> dict:
        """Helper: Chuyển đổi Objects DB thành Dictionary JSON"""
        dictionary_data = {}

        for w in words:
            variants_map = {
                v.variant_id: v.public_id 
                for v in w.videos
            }
            
            dictionary_data[w.slug] = {
                "word": w.word,
                "topics": w.topics or [], # Xử lý trường hợp null
                "variants": variants_map
            }

        return {
            "meta": {
                "region": region,
                "version": int(time.time()),
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
            "data": dictionary_data
        }

    def _upload_json_to_cloud(self, region: str, data: dict) -> str:
        try:
            # 1. Chuyển Dict -> String
            json_str = json.dumps(data, ensure_ascii=False)
            
            # 2. FIX LỖI Ở ĐÂY: Chuyển String -> Bytes
            # Cloudinary cần bytes để hiểu là "nội dung file"
            file_content = json_str.encode('utf-8')

            # Tên file cố định trên Cloudinary
            public_id = f"app_config/dictionary_{region}.json"

            print(f"📦 Uploading config: {public_id}")
            
            response = cloudinary.uploader.upload(
                file_content,         # <-- Truyền bytes vào đây
                resource_type="raw",  # Bắt buộc là 'raw'
                public_id=public_id,
                overwrite=True,       # Ghi đè file cũ
                invalidate=True,      # Xóa cache CDN cũ
                type="upload"
            )
            return response.get("secure_url")

        except Exception as e:
            print(f"❌ Cloudinary Error: {str(e)}")
            raise CloudinaryUploadError(f"Lỗi upload: {str(e)}")