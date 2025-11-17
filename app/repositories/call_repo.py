from datetime import datetime
from app.db.database import SessionLocal
from app.models.call import Call

class CallRepository:
    def __init__(self):
        self.db = SessionLocal()
    


    def create_call(self, caller_id: int, callee_id: int, call_type: str ):
        call = Call(
            caller_id=caller_id,
            callee_id=callee_id,
            call_type=call_type
        )
        self.db.add(call)
        self.db.commit()
        self.db.refresh(call)
        return call
    
    def end_call(self, call_id: int):
        call = self.db.query(Call).filter(Call.id == call_id).first()
        if call:
            call.ended_at = datetime.utcnow()
            call.status = "ended"
            self.db.commit()
            self.db.refresh(call)
        return call