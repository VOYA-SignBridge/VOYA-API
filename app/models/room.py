# app/models/room.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from app.db.database import Base



class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(12), unique=True, index=True)        # ví dụ 6-10 ký tự
    link = Column(String(255), unique=True)                   # deep-link/URL để join
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_locked = Column(Boolean, default=False)                # khoá phòng (owner)
    expires_at = Column(DateTime, nullable=True)              # hết hạn
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", foreign_keys=[created_by])