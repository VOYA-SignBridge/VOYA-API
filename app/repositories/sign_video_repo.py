from sqlalchemy.orm import Session, joinedload
from app.models.sign_video import DictionaryWord, WordVideo

class VideoRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_word(self, word_text: str, slug: str, region: str, topics: str) -> DictionaryWord:
        word_obj = self.db.query(DictionaryWord).filter(
            DictionaryWord.slug == slug,
            DictionaryWord.region == region
        ).first()

        if not word_obj:
            word_obj = DictionaryWord(
                word=word_text,
                slug=slug,
                region=region,
                topics=topics
            )
            self.db.add(word_obj)
            # CHỈ FLUSH, KHÔNG COMMIT
            self.db.flush() 
            self.db.refresh(word_obj) # Lấy ID để dùng ngay
        
        return word_obj

    def upsert_video_metadata(self, word_id: int, variant: str, version: str, public_id: str, cloud_ver: int):
        video_obj = self.db.query(WordVideo).filter(
            WordVideo.word_id == word_id,
            WordVideo.variant_id == variant,
            WordVideo.version_str == version
        ).first()

        if video_obj:
            video_obj.public_id = public_id
            video_obj.cloud_version = cloud_ver
        else:
            video_obj = WordVideo(
                word_id=word_id,
                variant_id=variant,
                version_str=version,
                public_id=public_id,
                cloud_version=cloud_ver,
            )
            self.db.add(video_obj)
        
        # ✅ THAY BẰNG: flush() để DB biết sự tồn tại, nhưng chưa chốt sổ
        self.db.flush() 
        return video_obj
    


    def get_all_videos_with_details(self):
        """
        Lấy danh sách video kèm thông tin từ vựng (Word)
        Sử dụng joinedload để tránh lỗi N+1 query
        """
        return self.db.query(WordVideo)\
            .options(joinedload(WordVideo.word_rel))\
            .order_by(WordVideo.id.desc())\
            .all()

    def get_video_by_id(self, video_id: int):
        return self.db.query(WordVideo).filter(WordVideo.id == video_id).first()

    def delete_video(self, video: WordVideo):
        self.db.delete(video)
        # Lưu ý: Repository không commit, Service sẽ quyết định khi nào commit
        self.db.flush()
    # Thêm hàm này để Service gọi khi xong hết mọi việc
    def commit_changes(self):
        self.db.commit()