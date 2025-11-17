from sqlalchemy import Column, Integer, String
from app.db.database import Base
from datetime import datetime
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    supabase_id = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default="normal")  # 'normal' hoặc 'deaf'
    created_at = Column(String, default=datetime.utcnow)
