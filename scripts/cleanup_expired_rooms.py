from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import settings
from app.services.room_cleanup_service import RoomCleanupService


def main() -> int:
    parser = argparse.ArgumentParser(description="Delete expired rooms older than the retention period.")
    parser.add_argument(
        "--retention-days",
        type=int,
        default=getattr(settings, "room_cleanup_retention_days", 7),
        help="Keep rooms for this many days after expires_at before deleting.",
    )
    args = parser.parse_args()

    service = RoomCleanupService(retention_days=args.retention_days)
    deleted = service.run_once()
    print(f"Deleted {deleted} expired rooms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
