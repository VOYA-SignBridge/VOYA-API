from __future__ import annotations

import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.repositories.room_repo import RoomRepository

logger = logging.getLogger(__name__)


class RoomCleanupService:
    def __init__(self, retention_days: int = 7):
        self.retention_days = max(0, int(retention_days))

    def run_once(self) -> int:
        db: Session = SessionLocal()
        try:
            repo = RoomRepository(db)
            cutoff = datetime.utcnow() - timedelta(days=self.retention_days)
            deleted = repo.cleanup_expired_rooms(cutoff)
            if deleted:
                logger.info("[RoomCleanup] removed %s expired rooms older than %s", deleted, cutoff.isoformat())
            return deleted
        except Exception:
            logger.exception("[RoomCleanup] cleanup failed")
            db.rollback()
            return 0
        finally:
            db.close()
