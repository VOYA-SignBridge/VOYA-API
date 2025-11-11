from fastapi import HTTPException
from app.repositories.friendship_repo import FriendshipRepository
from app.models.user import User

class FriendshipService:
    def __init__(self, db):
        self.db = db
        self.repo = FriendshipRepository(db)

    def send_request(self, current_user: User, friend_email: str):
        # find by email
        friend = self.db.query(User).filter(User.email == friend_email).first()
        if not friend:
            raise HTTPException(status_code=404, detail="User not found")

        if friend.id == current_user.id:
            raise HTTPException(status_code=400, detail="You cannot add yourself")

        # check relationship
        existing = self.repo.get_friendship(current_user.id, friend.id)
        if existing:
            raise HTTPException(status_code=400, detail="Friendship already exists")

        friendship = self.repo.create_friendship(current_user.id, friend.id)
        return {"message": f"Friend request sent to {friend.email}", "data": friendship}

    def accept_request(self, current_user: User, friend_email: str):
        friend = self.db.query(User).filter(User.email == friend_email).first()
        if not friend:
            raise HTTPException(status_code=404, detail="User not found")

        friendship = self.repo.get_friendship(current_user.id, friend.id)
        if not friendship or friendship.status != "pending":
            raise HTTPException(status_code=400, detail="No pending request found")

        updated = self.repo.update_status(friendship, "accepted")
        return {"message": f"Friend request from {friend.email} accepted", "data": updated}

    def list_friends(self, current_user: User):
        friendships = self.repo.get_user_friends(current_user.id)
        result = []
        for f in friendships:
            friend = f.friend if f.user_id == current_user.id else f.user
            result.append({
                "friend_id": friend.id,
                "friend_email": friend.email,
                "status": f.status,
                "created_at": f.created_at
            })
        return {"count": len(result), "friends": result}
