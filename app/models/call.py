from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class Call(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)
    caller_id= Column(Integer, ForeignKey("users.id"))
    callee_id = Column(Integer, ForeignKey("users.id"))
    call_type = Column(String(20), default="video")  # 'audio' or 'video'
    status = Column(String(20), default="ringing")  # 'ringing', 'accecpted', 'missed', 'ended'
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    #relationships
    caller = relationship("User", foreign_keys=[caller_id], backref="calls_made")
    callee = relationship("User", foreign_keys=[callee_id], backref="calls_received")