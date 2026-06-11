from datetime import date
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from models.appointment import Appointment
from repositories.base_repository import BaseRepository


class AppointmentRepository(BaseRepository[Appointment]):
    def __init__(self, session: Session) -> None:
        super().__init__(Appointment, session)

    def get_by_date(self, target_date: date) -> List[Appointment]:
        return (
            self.session.query(Appointment)
            .options(joinedload(Appointment.patient), joinedload(Appointment.doctor))
            .filter(Appointment.appointment_date == target_date)
            .order_by(Appointment.appointment_time)
            .all()
        )

    def get_by_patient(self, patient_id: int) -> List[Appointment]:
        return (
            self.session.query(Appointment)
            .filter(Appointment.patient_id == patient_id)
            .order_by(Appointment.appointment_date.desc())
            .all()
        )

    def count_today(self) -> int:
        return (
            self.session.query(Appointment)
            .filter(
                Appointment.appointment_date == date.today(),
                Appointment.status.in_(["Scheduled", "Confirmed"]),
            )
            .count()
        )
