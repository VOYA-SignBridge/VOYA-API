# app/services/user_service.py
from app.repositories.user_repo import UserRepository

class UserService:
    def __init__(self, db):
        self.db = db
        self.repo = UserRepository(db)

    def get_or_create_user(self, payload: dict):
        supabase_id = payload["sub"]
        email = payload.get("email")

        user = self.repo.get_by_supabase_id(supabase_id)

        if user:
            return user
        
        return self.repo.create_from_supabase(
            supabase_id=supabase_id,
            email=email,
            full_name=email.split("@")[0]
        )
