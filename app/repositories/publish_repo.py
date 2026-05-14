from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from app.models.app_config import AppConfig
from app.models.sign_video import DictionaryWord
from app.core.exceptions import DatabaseOperationalError

class PublishRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_words_with_videos_by_region(self, region: str) -> list[DictionaryWord]:
        try:
            # Sử dụng joinedload để tối ưu query (Eager Loading)
            # Tránh lỗi N+1 query khi loop qua danh sách
            query = self.db.query(DictionaryWord)\
                .options(joinedload(DictionaryWord.videos))\
                .filter(DictionaryWord.region == region)
            
            return query.all()
            
        except SQLAlchemyError as e:
            # Log lỗi tại đây nếu có hệ thống log (Sentry/CloudWatch)
            print(f"❌ DB Error: {str(e)}")
            raise DatabaseOperationalError(f"Lỗi truy vấn database cho vùng: {region}")
    def update_app_version(self, region: str, version: int):
        """Lưu version mới nhất vào DB"""
        config_key = f"version_{region}"
        # Tìm xem đã có chưa
        config = self.db.query(AppConfig).filter(AppConfig.key == config_key).first()
        
        if config:
            config.value = str(version) # Cập nhật
        else:
            new_config = AppConfig(key=config_key, value=str(version)) # Tạo mới
            self.db.add(new_config)
            
        self.db.commit()

    def get_app_version(self, region: str) -> int:
        config_key = f"version_{region}"
        config = self.db.query(AppConfig).filter(AppConfig.key == config_key).first()
        return int(config.value) if config else 0