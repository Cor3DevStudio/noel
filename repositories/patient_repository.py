from datetime import date
from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from models.patient import Patient
from repositories.base_repository import BaseRepository


class PatientRepository(BaseRepository[Patient]):
    def __init__(self, session: Session) -> None:
        super().__init__(Patient, session)

    def search(self, query: str, include_archived: bool = False) -> List[Patient]:
        q = self.session.query(Patient)
        if not include_archived:
            q = q.filter(Patient.is_archived == False)
        if query:
            pattern = f"%{query}%"
            q = q.filter(
                or_(
                    Patient.first_name.ilike(pattern),
                    Patient.last_name.ilike(pattern),
                    Patient.patient_number.ilike(pattern),
                    Patient.philhealth_number.ilike(pattern),
                    Patient.contact_number.ilike(pattern),
                )
            )
        return q.order_by(Patient.last_name, Patient.first_name).limit(100).all()

    def find_by_name(
        self,
        first_name: str,
        last_name: str,
        exclude_id: int | None = None,
    ) -> List[Patient]:
        """Return active patients whose first + last name match (case-insensitive)."""
        q = (
            self.session.query(Patient)
            .filter(
                Patient.is_archived == False,
                Patient.first_name.ilike(first_name.strip()),
                Patient.last_name.ilike(last_name.strip()),
            )
        )
        if exclude_id is not None:
            q = q.filter(Patient.id != exclude_id)
        return q.all()

    def get_active_count(self) -> int:
        return self.session.query(Patient).filter(Patient.is_archived == False).count()

    def get_monthly_new_count(self) -> int:
        today = date.today()
        start = today.replace(day=1)
        return (
            self.session.query(Patient)
            .filter(Patient.created_at >= start, Patient.is_archived == False)
            .count()
        )

    def get_recent(self, limit: int = 10) -> List[Patient]:
        return (
            self.session.query(Patient)
            .filter(Patient.is_archived == False)
            .order_by(Patient.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_next_number(self) -> str:
        from utils.helpers import generate_patient_number
        count = self.count() + 1
        return generate_patient_number(count)

    def archive(self, patient: Patient) -> Patient:
        patient.is_archived = True
        self.session.flush()
        return patient
