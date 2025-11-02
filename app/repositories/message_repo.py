from sqlalchemy.orm import Session
from app.models.message import Message


class MessageRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_message(self, sender_id: int, receiver_id: int, content: str):
        message= Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message
    

    def get_conversation(self, user_id:int, friend_id: int):
        return self.db.query(Message).filter(
            ((Message.sender_id == user_id) & (Message.receiver_id == friend_id)) |
            ((Message.sender_id == friend_id) & (Message.receiver_id == user_id))
        ).order_by(Message.created_at).all()