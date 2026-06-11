from typing import List, Optional

from sqlalchemy.orm import Session

from models.audit import ActivityLog, AuditLog
from models.settings_model import ClinicSettings
from repositories.base_repository import BaseRepository


class SettingsRepository(BaseRepository[ClinicSettings]):
    def __init__(self, session: Session) -> None:
        super().__init__(ClinicSettings, session)

    def get_settings(self) -> ClinicSettings:
        settings = self.session.query(ClinicSettings).first()
        if not settings:
            settings = self.create({"clinic_name": "Clinic Management System"})
        return settings


class ActivityLogRepository(BaseRepository[ActivityLog]):
    def __init__(self, session: Session) -> None:
        super().__init__(ActivityLog, session)

    def get_recent(self, limit: int = 100) -> List[ActivityLog]:
        return (
            self.session.query(ActivityLog)
            .order_by(ActivityLog.created_at.desc())
            .limit(limit)
            .all()
        )


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, session: Session) -> None:
        super().__init__(AuditLog, session)

    def get_recent(self, limit: int = 100) -> List[AuditLog]:
        return (
            self.session.query(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )
