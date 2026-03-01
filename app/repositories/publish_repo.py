from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
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