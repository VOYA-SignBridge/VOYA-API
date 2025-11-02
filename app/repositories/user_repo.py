from sqlalchemy.orm import Session
from app.models.user import User


def get_user_by_email(db: Session, email: str) -> User:
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, email: str, password_hash: str, full_name: str):
    new_user = User(email=email, full_name=full_name, hashed_password=password_hash)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
