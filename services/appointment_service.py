"""Appointment management service."""

from datetime import date, time
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from models.appointment import Appointment
from repositories.appointment_repository import AppointmentRepository
from utils.security import session_manager


class AppointmentService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = AppointmentRepository(session)

    def create(self, data: dict) -> Tuple[bool, str, Optional[Appointment]]:
        user = session_manager.get_current_user()
        data["created_by"] = user["id"] if user else None
        data.setdefault("status", "Scheduled")
        appointment = self.repo.create(data)
        return True, "Appointment scheduled successfully.", appointment

    def update(self, appointment_id: int, data: dict) -> Tuple[bool, str]:
        appointment = self.repo.get_by_id(appointment_id)
        if not appointment:
            return False, "Appointment not found."
        self.repo.update(appointment, data)
        return True, "Appointment updated successfully."

    def cancel(self, appointment_id: int) -> Tuple[bool, str]:
        return self.update(appointment_id, {"status": "Cancelled"})

    def get_by_date(self, target_date: date) -> List[Appointment]:
        return self.repo.get_by_date(target_date)

    def get_today(self) -> List[Appointment]:
        return self.repo.get_by_date(date.today())

    def get_by_patient(self, patient_id: int) -> List[Appointment]:
        return self.repo.get_by_patient(patient_id)

    def count_today(self) -> int:
        return self.repo.count_today()

    def get_by_id(self, appointment_id: int) -> Optional[Appointment]:
        return self.repo.get_by_id(appointment_id)
