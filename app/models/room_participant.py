from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from app.db.database import Base

class RoomParticipant(Base):
    __tablename__ = "room_participants"
    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # anonymous có thể None
    display_name = Column(String(64), nullable=True)                  # cho khách không login
    role = Column(String(12), default="normal")                       # normal | deaf | mod | owner
    joined_at = Column(DateTime, default=datetime.utcnow)
    left_at = Column(DateTime, nullable=True)

    __table_args__ = (UniqueConstraint("room_id","user_id", name="uq_room_user"),)