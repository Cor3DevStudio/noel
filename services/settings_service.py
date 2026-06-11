"""Clinic settings and backup service."""

import shutil
import subprocess
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Tuple

from sqlalchemy.orm import Session

from config.settings import BACKUP_DIR, DB_HOST, DB_NAME, DB_PASSWORD, DB_USER
from models.settings_model import ClinicSettings
from repositories.settings_repository import AuditLogRepository, SettingsRepository
from services.activity_service import ActivityService


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
        backup_file = BACKUP_DIR / f"clinic_backup_{timestamp}.sql"
        try:
            cmd = [
                "mysqldump",
                f"--host={DB_HOST}",
                f"--user={DB_USER}",
            ]
            if DB_PASSWORD:
                cmd.append(f"--password={DB_PASSWORD}")
            cmd.extend([DB_NAME])
            with open(backup_file, "w", encoding="utf-8") as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0:
                return False, f"Backup failed: {result.stderr}", ""
            self.activity.log(
                "BACKUP", "Settings",
                f"Database backup created: {backup_file.name}",
            )
            return True, "Database backup created successfully.", str(backup_file)
        except FileNotFoundError:
            return False, "mysqldump not found. Install MySQL client tools.", ""
        except Exception as exc:
            return False, f"Backup error: {exc}", ""

    def restore_database(self, backup_path: str) -> Tuple[bool, str]:
        path = Path(backup_path)
        if not path.exists():
            return False, "Backup file not found."
        try:
            cmd = [
                "mysql",
                f"--host={DB_HOST}",
                f"--user={DB_USER}",
            ]
            if DB_PASSWORD:
                cmd.append(f"--password={DB_PASSWORD}")
            cmd.append(DB_NAME)
            with open(path, "r", encoding="utf-8") as f:
                result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0:
                return False, f"Restore failed: {result.stderr}"
            self.activity.log(
                "RESTORE", "Settings",
                f"Database restored from {path.name}",
            )
            return True, "Database restored successfully."
        except FileNotFoundError:
            return False, "mysql client not found. Install MySQL client tools."
        except Exception as exc:
            return False, f"Restore error: {exc}"
