from app.db.database import Base, engine
from app.models.sign import Sign
from app.models.sign_alias import SignAlias

def init_db():
    Base.metadata.create_all(bind=engine)
