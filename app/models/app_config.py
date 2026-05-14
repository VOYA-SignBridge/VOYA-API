from sqlalchemy import Column, String
from app.db.database import Base

class AppConfig(Base):
    __tablename__ = "app_configs"
    
    key = Column(String, primary_key=True, index=True) 
    value = Column(String)