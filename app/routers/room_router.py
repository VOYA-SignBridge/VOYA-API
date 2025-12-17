# app/routers/room_router.py
from http.client import HTTPException
import json
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.redis_client import redis_client
from app.db.database import get_db
from app.services.room_service import RoomService
from app.core.dependencies import get_current_user
router = APIRouter(prefix="/rooms", tags=["Rooms"])


#step 1:FE call to create room
@router.post("/create")
def create_room(
        ttl_minutes: int|None = 120, 
        db: Session = Depends(get_db), 
        me = Depends(get_current_user)):
    print("Current userID:" , me.id)
    room_service = RoomService(db); 
    
    return room_service.create_room(me.id, ttl_minutes)

#step 2: FE call to join room
@router.post("/{code}/join")
def join_room(code: str,
                role: str = Query("normal", 
                pattern="^(normal|deaf)$"),    
                db: Session = Depends(get_db), 
                me = Depends(get_current_user)):
    
    display_name = me.full_name
    user_id = me.id if me else None
    room_service = RoomService(db); 
    return room_service.join_room(
                                    code, 
                                    user_id, 
                                    display_name, 
                                    role)

@router.post("/{code}/leave")
def leave_room(
                code: str, display_name: str|None = None, 
                db: Session = Depends(get_db), 
                me = Depends(get_current_user)):
    user_id = me.id if me else None
    room_service = RoomService(db); 
    return room_service.leave_room(
        code, 
        user_id, 
        display_name)

@router.get("/{code}/participants")
def participants(
                code: str, 
                db: Session = Depends(get_db),
                me = Depends(get_current_user)
                ):
    room_service = RoomService(db); 
    return room_service.list_participants(code)

@router.post("/{code}/end")
async def end_room(
    code: str,
    db: Session = Depends(get_db),
    me = Depends(get_current_user),
):
    service = RoomService(db)
    room = service.end_room(code, me.id)

    #  Publish event room.ended cho tất cả client trong room
    await redis_client.publish(
        f"room:{code}",
        json.dumps({
            "type": "room.ended"
        })
    )

    return {
        "room_code": room.code,
        "ended": True,
    }

@router.get("/{code}/room")
def get_room(code: str, db: Session = Depends(get_db), me = Depends(get_current_user)):
    room_service = RoomService(db)

    room = room_service.get_room_by_code(code)
    return room
