"""Patient management service."""

from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from models.patient import Patient
from repositories.patient_repository import PatientRepository
from repositories.settings_repository import AuditLogRepository
from services.activity_service import ActivityService
from utils.security import session_manager


class PatientService:
    def __init__(self, session: Session, activity_service: ActivityService | None = None) -> None:
        self.session = session
        self.repo = PatientRepository(session)
        self.activity = activity_service or ActivityService(session)
        self.audit_repo = AuditLogRepository(session)

    def register(self, data: dict) -> Tuple[bool, str, Optional[Patient]]:
        first = (data.get("first_name") or "").strip()
        last  = (data.get("last_name")  or "").strip()

        duplicates = self.repo.find_by_name(first, last)
        if duplicates:
            names = ", ".join(
                f"{p.full_name} ({p.patient_number})" for p in duplicates
            )
            return (
                False,
                f"A patient with the name '{first} {last}' already exists:\n{names}\n\n"
                f"Please verify this is a different person before registering.",
                None,
            )

        data["patient_number"] = self.repo.get_next_number()
        data.setdefault("is_archived", False)
        patient = self.repo.create(data)
        self._audit("CREATE", patient.id, None, data)
        self._log(f"Registered patient {patient.patient_number}", "CREATE")
        return True, "Patient registered successfully.", patient

    def update(self, patient_id: int, data: dict) -> Tuple[bool, str]:
        patient = self.repo.get_by_id(patient_id)
        if not patient:
            return False, "Patient not found."

        first = (data.get("first_name") or "").strip()
        last  = (data.get("last_name")  or "").strip()

        duplicates = self.repo.find_by_name(first, last, exclude_id=patient_id)
        if duplicates:
            names = ", ".join(
                f"{p.full_name} ({p.patient_number})" for p in duplicates
            )
            return (
                False,
                f"Another patient named '{first} {last}' already exists:\n{names}\n\n"
                f"Please verify this is a different person before saving.",
            )

        old = {"patient_number": patient.patient_number, "full_name": patient.full_name}
        self.repo.update(patient, data)
        self._audit("UPDATE", patient_id, old, data)
        self._log(f"Updated patient {patient.patient_number}")
        return True, "Patient updated successfully."

    def archive(self, patient_id: int) -> Tuple[bool, str]:
        patient = self.repo.get_by_id(patient_id)
        if not patient:
            return False, "Patient not found."
        self.repo.archive(patient)
        self._log(f"Archived patient {patient.patient_number}", "ARCHIVE")
        return True, "Patient archived successfully."

    def search(self, query: str) -> List[Patient]:
        return self.repo.search(query)

    def get_by_id(self, patient_id: int) -> Optional[Patient]:
        return self.repo.get_by_id(patient_id)

    def get_recent(self, limit: int = 10) -> List[Patient]:
        return self.repo.get_recent(limit)

    def get_count(self) -> int:
        return self.repo.get_active_count()

    def _log(self, description: str, action: str = "UPDATE") -> None:
        self.activity.log(action, "Patients", description)

    def _audit(self, action: str, record_id: int, old: dict | None, new: dict) -> None:
        user = session_manager.get_current_user()
        self.audit_repo.create({
            "user_id": user["id"] if user else None,
            "table_name": "patients",
            "record_id": record_id,
            "action": action,
            "old_values": old,
            "new_values": new,
        })
