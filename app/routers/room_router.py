# app/routers/room_router.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.room_service import RoomService
from app.core.dependencies import get_current_user
router = APIRouter(prefix="/rooms", tags=["Rooms"])


#step 1:FE call to create room
@router.post("/create")
def create_room(
    ttl_minutes: int | None = 120,
    user_id: int | None = Query(None, description="Optional creator ID"),
    db: Session = Depends(get_db),
    me: dict | None = Depends(get_current_user),
):
    room_service = RoomService(db)
    creator_id = user_id

    if creator_id is None and me:
        creator_id = getattr(me, "id", None) or getattr(me, "supabase_id", None)

    return room_service.create_room(creator_id, ttl_minutes)

#step 2: FE call to join room
@router.post("/{code}/join")
def join_room(code: str,
                role: str = Query("normal",
                pattern="^(normal|deaf)$"),
                display_name: str | None = Query(None, description="Optional display name"),
                user_id: int | None = Query(None, description="Optional user ID"),
                db: Session = Depends(get_db),
                me: dict|None = Depends(get_current_user)):

    resolved_display_name = display_name
    if resolved_display_name is None and me:
        resolved_display_name = getattr(me, "full_name", None)
    if resolved_display_name is None:
        resolved_display_name = "Guest"

    resolved_user_id = user_id
    if resolved_user_id is None and me:
        resolved_user_id = getattr(me, "id", None) or getattr(me, "supabase_id", None)

    room_service = RoomService(db)
    return room_service.join_room(
                                    code,
                                    resolved_user_id,
                                    resolved_display_name,
                                    role)

@router.post("/{code}/leave")
def leave_room(
    code: str,
    display_name: str | None = None,
    user_id: int | None = Query(None, description="Optional user ID"),
    db: Session = Depends(get_db),
    me: dict | None = Depends(get_current_user),
):
    resolved_user_id = user_id
    if resolved_user_id is None and me:
        resolved_user_id = getattr(me, "id", None) or getattr(me, "supabase_id", None)

    room_service = RoomService(db)
    return room_service.leave_room(code, resolved_user_id, display_name)

@router.get("/{code}/participants")
def participants(code: str, db: Session = Depends(get_db)):
    room_service = RoomService(db); return room_service.list_participants(code)
