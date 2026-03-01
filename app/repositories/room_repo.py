import secrets, string
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models.room import Room
from app.models.room_participant import RoomParticipant

class RoomRepository:
    def __init__(self, db: Session):
        self.db = db

    #Generate a random room code
    def _gen_code(self, n=8):
        alphabet = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(n))

    #Create a new room ttl: time to live
    def create_room(self, created_by: int|None, ttl_minutes: int|None = 120):
        code = self._gen_code()
        link = f"voyaapp/room/{code}"
        expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes) if ttl_minutes else None
        room = Room(code=code, link=link, created_by=created_by, expires_at=expires_at)
        self.db.add(room); self.db.commit(); self.db.refresh(room)
        return room


    #Get room by code
    def get_room_by_code(self, code: str) -> Room|None:
        return self.db.query(Room).filter(Room.code == code).first()

    # room_repo.py

    def add_participant(self, room_id, user_id, display_name, role):
        # 1. Check nếu đã tồn tại participant
        existing_participant = (
            self.db.query(RoomParticipant)
            .filter(RoomParticipant.room_id == room_id,
                    RoomParticipant.user_id == user_id)
            .first()
        )

        if existing_participant:
            # update left_at = null
            existing_participant.left_at = None
            existing_participant.display_name = display_name
            existing_participant.role = role
            self.db.commit()
            self.db.refresh(existing_participant)
            return existing_participant

        # 2. Nếu chưa tồn tại → INSERT mới
        p = RoomParticipant(
            room_id=room_id,
            user_id=user_id,
            display_name=display_name,
            role=role
        )
        self.db.add(p)
        self.db.commit()
        self.db.refresh(p)
        return p

    def mark_participant_left(
        self,
        room_id: int,
        user_id: Optional[int] = None,
        display_name: Optional[str] = None,
    ) -> Optional[RoomParticipant]:
        """
        Đánh dấu một participant trong room đã rời đi (set left_at).

        Ưu tiên tìm theo user_id, nếu không có thì fallback sang display_name.
        Trả về bản ghi RoomParticipant đã được cập nhật (hoặc None nếu không tìm thấy).
        """

        # Không có đủ thông tin để xác định participant
        if user_id is None and not display_name:
            return None

        query = (
            self.db
            .query(RoomParticipant)
            .filter(RoomParticipant.room_id == room_id)
        )

        if user_id is not None:
            # Ưu tiên dùng user_id vì đây là định danh duy nhất
            query = query.filter(RoomParticipant.user_id == user_id)
        else:
            # Fallback theo display_name (ít an toàn hơn, có thể trùng)
            query = query.filter(RoomParticipant.display_name == display_name)

        # Lấy lần join mới nhất của participant này trong room
        latest_participation = (
            query
            .order_by(RoomParticipant.joined_at.desc())
            .first()
        )

        # Nếu tìm được và chưa set left_at thì cập nhật
        if latest_participation and latest_participation.left_at is None:
            latest_participation.left_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(latest_participation)

        return latest_participation

    def mark_all_left(self, room_id: int):
        rows = (
            self.db.query(RoomParticipant)
            .filter(RoomParticipant.room_id == room_id, RoomParticipant.left_at == None)
            .all()
        )
        for p in rows:
            p.left_at = datetime.utcnow()

        self.db.commit()
    #list participaints
    def list_participants(self, room_id: int):
        return self.db.query(RoomParticipant).filter(RoomParticipant.room_id==room_id, RoomParticipant.left_at==None).all()


    def delete_room(self, room_id: int):
        room = self.db.query(Room).filter(Room.id == room_id).first()
        if not room:
            return None
        self.db.delete(room)
        self.db.commit()
        return room

    

    
