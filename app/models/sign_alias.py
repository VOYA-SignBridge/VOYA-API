from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class SignAlias(Base):
    __tablename__ = "sign_aliases"

    id = Column(Integer, primary_key=True, index=True)
    sign_id = Column(Integer, ForeignKey("signs.id"), nullable=False)
    phrase_raw = Column(String(255), nullable=False)
    phrase_normalized = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # many-to-one: SignAlias -> Sign
    sign = relationship(
        "Sign",
        back_populates="aliases"
    )
