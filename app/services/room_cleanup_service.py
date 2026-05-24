from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.repositories.room_repo import RoomRepository

logger = logging.getLogger(__name__)


class RoomCleanupService:
    def __init__(self, retention_days: int = 7, interval_hours: int = 24):
        self.retention_days = max(0, int(retention_days))
        self.interval_seconds = max(60, int(interval_hours) * 3600)
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="room-cleanup-job")
        self._thread.start()
        logger.info(
            "[RoomCleanup] started retention_days=%s interval_hours=%s",
            self.retention_days,
            self.interval_seconds // 3600,
        )

    def stop(self):
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        logger.info("[RoomCleanup] stopped")

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

    def _run(self):
        self.run_once()
        while not self._stop_event.wait(self.interval_seconds):
            self.run_once()

