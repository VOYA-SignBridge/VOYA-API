from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.friendship_service import FriendshipService
from app.models.user import User
from app.core.dependencies import get_current_user
router = APIRouter(prefix="/friends", tags=["Friendship"])



@router.post("/request")
def send_friend_request(friend_email: str, 
                        db: Session = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    service = FriendshipService(db)
    return service.send_request(current_user, friend_email)

@router.patch("/accept")
def accept_friend_request(friend_email: str, db: Session = Depends(get_db),
                          current_user: User = Depends(get_current_user)):
    service = FriendshipService(db)
    return service.accept_request(current_user, friend_email)

@router.get("/me")
def list_my_friends(db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    service = FriendshipService(db)
    return service.list_friends(current_user)
