from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class Sign(Base):
    __tablename__ = "signs"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, index=True)
    language = Column(String(50), nullable=False)
    public_id = Column(String(255), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # one-to-many: Sign -> SignAlias
    aliases = relationship(
        "SignAlias",
        back_populates="sign",
        cascade="all, delete-orphan"
    )
