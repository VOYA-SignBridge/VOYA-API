from sqlalchemy.orm import Session
from datetime import datetime
from app.models.friendship import Friendship

class FriendshipRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_friendship(self, user_id: int, friend_id: int, status: str = "pending"):
        friendship = Friendship(
            user_id=user_id,
            friend_id=friend_id,
            status=status,
            created_at=datetime.utcnow()
        )
        self.db.add(friendship)
        self.db.commit()
        self.db.refresh(friendship)
        return friendship

    def get_friendship(self, user_id: int, friend_id: int):
        return (
            self.db.query(Friendship)
            .filter(
                ((Friendship.user_id == user_id) & (Friendship.friend_id == friend_id))
                | ((Friendship.user_id == friend_id) & (Friendship.friend_id == user_id))
            )
            .first()
        )

    def update_status(self, friendship: Friendship, new_status: str):
        friendship.status = new_status
        self.db.commit()
        self.db.refresh(friendship)
        return friendship

    def get_user_friends(self, user_id: int):
        return (
            self.db.query(Friendship)
            .filter(
                ((Friendship.user_id == user_id) | (Friendship.friend_id == user_id))
                & (Friendship.status == "accepted")
            )
            .all()
        )
