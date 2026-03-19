
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.repositories.room_repo import RoomRepository
from app.core.redis_client import redis_client
class RoomService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = RoomRepository(db)

    def create_room(self, host_id: int|None, ttl_minutes: int|None=120):
        print("Creating room for user: ", host_id)
        room = self.repo.create_room(host_id, ttl_minutes)
        return {"code": room.code, 
                "link": room.link, 
                "expires_at": room.expires_at    
                }

    def join_room(self, code: str, user_id: int|None, display_name: str|None, role: str):
        room = self.repo.get_room_by_code(code)
        if not room: 
            raise HTTPException(404, "Room not found")
        if room.expires_at and room.expires_at < datetime.utcnow():
            raise HTTPException(410, "Room expired")
        if room.is_locked and (not user_id or user_id != room.created_by):
            raise HTTPException(403, "Room is locked")
        participant= self.repo.add_participant(room.id, user_id, display_name, role)
        return {
            "room_code": room.code,
            "participant": {
                "id": participant.id,
                "user_id": user_id,
                "display_name": display_name,
                "role": role
            }
            }

    def leave_room(self, code: str, user_id: int|None, display_name: str|None):
        room = self.repo.get_room_by_code(code)
        if not room: raise HTTPException(404, "Room not found")
        self.repo.mark_participant_left(
            room.id, 
            user_id, 
            display_name)
        return {"room_code": room.code, "left": True}

    def list_participants(self, code: str):
        room = self.repo.get_room_by_code(code)
        if not room: raise HTTPException(404, "Room not found")
        people = self.repo.list_participants(room.id)
        return [
            {
            "participant_id": p.id, 
            "user_id": p.user_id, 
             "display_name": p.display_name, 
             "role": p.role, 
             "joined_at": p.joined_at
             } 
             for p in people]
    def end_room(self, code: str, user_id: int):
        room = self.repo.get_room_by_code(code)
        if not room:
            raise HTTPException(404, "Room not found")

        if room.created_by != user_id:
            raise HTTPException(403, "Only the room creator can end the room")

        # Đánh dấu phòng đã khoá + hết hạn
        room.is_locked = True
        room.expires_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(room)

        # Đánh dấu tất cả participant còn active là left
        self.repo.mark_all_left(room.id)

        return room
    def get_room_by_code(self, code: str):
        room = self.repo.get_room_by_code(code)
        if not room:
            raise HTTPException(404, "Room not found")
        return {
            "code": room.code,
            "owner_id": room.created_by,
            "expires_at": room.expires_at,
            "is_locked": room.is_locked
        }