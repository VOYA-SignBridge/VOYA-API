# app/repositories/user_repo.py
from app.models.user import User

class UserRepository:
    def __init__(self, db):
        self.db = db

    def get_by_supabase_id(self, supabase_id: str):
        return self.db.query(User).filter(User.supabase_id == supabase_id).first()

    def create_from_supabase(self, supabase_id: str, email: str, full_name: str):
        user = User(
            supabase_id=supabase_id,
            email=email,
            full_name=full_name,
            hashed_password="",   # Supabase quản lý, backend để trống
            role="normal"
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
