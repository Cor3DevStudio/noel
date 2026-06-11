"""Consultation and prescription service."""

from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from models.consultation import Consultation
from models.prescription import Prescription, PrescriptionItem
from repositories.consultation_repository import ConsultationRepository
from utils.security import session_manager


class ConsultationService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = ConsultationRepository(session)

    def create(self, data: dict) -> Tuple[bool, str, Optional[Consultation]]:
        user = session_manager.get_current_user()
        if user and "doctor_id" not in data:
            data["doctor_id"] = user["id"]
        consultation = self.repo.create(data)
        return True, "Consultation started.", consultation

    def update(self, consultation_id: int, data: dict) -> Tuple[bool, str]:
        consultation = self.repo.get_by_id(consultation_id)
        if not consultation:
            return False, "Consultation not found."
        self.repo.update(consultation, data)
        return True, "Consultation updated."

    def complete(self, consultation_id: int) -> Tuple[bool, str]:
        return self.update(consultation_id, {"status": "Completed"})

    def get_by_patient(self, patient_id: int) -> List[Consultation]:
        return self.repo.get_by_patient(patient_id)

    def get_with_details(self, consultation_id: int) -> Optional[Consultation]:
        return self.repo.get_with_details(consultation_id)

    def create_prescription(
        self, consultation_id: int, patient_id: int, items: List[dict], notes: str = ""
    ) -> Tuple[bool, str, Optional[Prescription]]:
        user = session_manager.get_current_user()
        prescription = Prescription(
            consultation_id=consultation_id,
            patient_id=patient_id,
            doctor_id=user["id"] if user else 1,
            doctor_signature=user["full_name"] if user else "",
            notes=notes,
        )
        self.session.add(prescription)
        self.session.flush()

        for item in items:
            self.session.add(PrescriptionItem(
                prescription_id=prescription.id,
                medicine_id=item.get("medicine_id"),
                medicine_name=item["medicine_name"],
                dosage=item.get("dosage", ""),
                frequency=item.get("frequency", ""),
                duration=item.get("duration", ""),
                quantity=int(item.get("quantity", 1)),
                instructions=item.get("instructions", ""),
            ))
        self.session.flush()
        return True, "Prescription created.", prescription
