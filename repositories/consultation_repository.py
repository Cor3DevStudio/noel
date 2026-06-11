from datetime import date, datetime
from typing import List

from sqlalchemy.orm import Session, joinedload

from models.consultation import Consultation
from repositories.base_repository import BaseRepository


class ConsultationRepository(BaseRepository[Consultation]):
    def __init__(self, session: Session) -> None:
        super().__init__(Consultation, session)

    def get_by_patient(self, patient_id: int) -> List[Consultation]:
        return (
            self.session.query(Consultation)
            .options(joinedload(Consultation.doctor))
            .filter(Consultation.patient_id == patient_id)
            .order_by(Consultation.consultation_date.desc())
            .all()
        )

    def count_today(self) -> int:
        today = date.today()
        return (
            self.session.query(Consultation)
            .filter(
                Consultation.consultation_date >= datetime.combine(today, datetime.min.time()),
                Consultation.consultation_date <= datetime.combine(today, datetime.max.time()),
            )
            .count()
        )

    def get_with_details(self, consultation_id: int) -> Consultation | None:
        return (
            self.session.query(Consultation)
            .options(
                joinedload(Consultation.patient),
                joinedload(Consultation.doctor),
                joinedload(Consultation.prescriptions),
            )
            .filter(Consultation.id == consultation_id)
            .first()
        )
