"""Clinic settings and backup service."""

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Tuple

from sqlalchemy.orm import Session

from config.settings import BACKUP_DIR
from database.connection import engine
from models.settings_model import ClinicSettings
from repositories.settings_repository import AuditLogRepository, SettingsRepository
from services.activity_service import ActivityService
from utils.db_backup import backup_database_json, restore_database_json


class SettingsService:
    def __init__(self, session: Session, activity_service: ActivityService | None = None) -> None:
        self.session = session
        self.repo = SettingsRepository(session)
        self.activity = activity_service or ActivityService(session)
        self.audit_repo = AuditLogRepository(session)

    def get_settings(self) -> ClinicSettings:
        return self.repo.get_settings()

    def update_settings(self, data: dict) -> Tuple[bool, str]:
        settings = self.repo.get_settings()
        if "consultation_fee" in data:
            try:
                new_fee = Decimal(str(data["consultation_fee"]))
                if new_fee != Decimal(str(settings.consultation_fee or 0)):
                    data["consultation_fee_effective_date"] = date.today()
            except Exception:
                pass
        self.repo.update(settings, data)
        changed = ", ".join(k.replace("_", " ") for k in data if data.get(k))
        self.activity.log(
            "UPDATE", "Settings",
            f"Updated hospital settings: {changed or 'configuration'}",
        )
        return True, "Settings updated successfully."

    def get_activity_logs(self, limit: int = 100):
        return self.activity.get_recent(limit)

    def get_activity_logs_enriched(self, limit: int = 100):
        return self.activity.get_recent_enriched(limit)

    def log_action(self, action: str, module: str, description: str) -> None:
        self.activity.log(action, module, description)

    def get_audit_logs(self, limit: int = 100):
        return self.audit_repo.get_recent(limit)

    def backup_database(self) -> Tuple[bool, str, str]:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUP_DIR / f"clinic_backup_{timestamp}.json"
        try:
            row_count = backup_database_json(engine, backup_file)
            self.activity.log(
                "BACKUP", "Settings",
                f"JSON database backup created: {backup_file.name} ({row_count} rows)",
            )
            self.session.commit()
            return (
                True,
                f"Database backup created ({row_count} rows).\nNo MySQL tools required.",
                str(backup_file),
            )
        except Exception as exc:
            self.session.rollback()
            return False, f"Backup error: {exc}", ""

    def restore_database(self, backup_path: str) -> Tuple[bool, str]:
        path = Path(backup_path)
        if not path.exists():
            return False, "Backup file not found."
        if path.suffix.lower() == ".sql":
            return (
                False,
                "Legacy .sql backups are no longer supported.\n"
                "Use a .json backup exported from this application.",
            )
        if path.suffix.lower() != ".json":
            return False, "Unsupported backup file. Please select a .json backup."
        try:
            row_count = restore_database_json(engine, path)
            self.activity.log(
                "RESTORE", "Settings",
                f"Database restored from {path.name} ({row_count} rows)",
            )
            self.session.commit()
            return (
                True,
                f"Database restored successfully ({row_count} rows).\n"
                "Please restart the application.",
            )
        except Exception as exc:
            self.session.rollback()
            return False, f"Restore error: {exc}"
