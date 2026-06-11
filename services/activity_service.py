"""Centralized user activity logging."""

from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from models.audit import ActivityLog
from repositories.settings_repository import ActivityLogRepository
from utils.security import session_manager


class ActivityService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = ActivityLogRepository(session)

    def log(self, action: str, module: str, description: str, user_id: Optional[int] = None) -> None:
        user = session_manager.get_current_user()
        self.repo.create({
            "user_id": user_id if user_id is not None else (user["id"] if user else None),
            "action": action,
            "module": module,
            "description": description,
        })

    def log_page_open(self, page_key: str, page_title: str) -> None:
        self.log("OPEN_PAGE", "Navigation", f"Opened {page_title} ({page_key})")

    def get_recent(self, limit: int = 100) -> List[ActivityLog]:
        return self.repo.get_recent(limit)

    def get_recent_enriched(self, limit: int = 100) -> List[Tuple[ActivityLog, str, str]]:
        return self.repo.get_recent_with_users(limit)
