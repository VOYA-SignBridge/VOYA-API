import time
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, JSON 
from app.db.database import Base

class DictionaryWord(Base):
    __tablename__ = "dictionary_words"

    id = Column(Integer, primary_key=True, index=True)
    word = Column(String, nullable=False)    
    slug = Column(String, nullable=False)    
    region = Column(String, default="vsl_common") 
    
    topics = Column(JSON, default=[]) 

    # Quan hệ 1-N
    videos = relationship("WordVideo", back_populates="word_rel")

    # Constraint: Mỗi vùng miền chỉ có 1 slug duy nhất
    __table_args__ = (UniqueConstraint('slug', 'region', name='uq_slug_region'),)

class WordVideo(Base):
    __tablename__ = "word_videos"

    id = Column(Integer, primary_key=True, index=True)
    word_id = Column(Integer, ForeignKey("dictionary_words.id", ondelete="CASCADE")) # Thêm CASCADE để xóa từ thì xóa luôn video
    
    variant_id = Column(String, nullable=False)   # 'actor_male', 'avatar_robot'
    version_str = Column(String, default="v1")    # 'v1'
    cloud_version = Column(String, nullable=True)  # Phiên bản trên Cloudinary để cache busting
    # Thông tin Cloudinary
    public_id = Column(String, nullable=False)    # Để tạo URL
    format = Column(String(10), default="mp4")    # mp4/webm
    resource_type = Column(String(20), default="video")

    word_rel = relationship("DictionaryWord", back_populates="videos")
    created_at = Column(BigInteger, nullable=False, default=lambda: int(time.time()))
    # Constraint: Một từ không thể có 2 video trùng variant và version
    __table_args__ = (UniqueConstraint('word_id', 'variant_id', 'version_str', name='uq_video_variant'),)



