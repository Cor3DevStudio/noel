"""Dashboard statistics service."""

from datetime import date
from typing import Any, Dict

from sqlalchemy.orm import Session

from repositories.appointment_repository import AppointmentRepository
from repositories.consultation_repository import ConsultationRepository
from repositories.medicine_repository import MedicineRepository
from repositories.patient_repository import PatientRepository
from services.billing_service import BillingService


class DashboardService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.patient_repo = PatientRepository(session)
        self.appointment_repo = AppointmentRepository(session)
        self.consultation_repo = ConsultationRepository(session)
        self.medicine_repo = MedicineRepository(session)
        self.billing_service = BillingService(session)

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_patients": self.patient_repo.get_active_count(),
            "today_appointments": self.appointment_repo.count_today(),
            "today_consultations": self.consultation_repo.count_today(),
            "today_revenue": self.billing_service.get_today_revenue(),
            "monthly_revenue": self.billing_service.get_monthly_revenue(),
            "low_stock_count": len(self.medicine_repo.get_low_stock()),
            "expiring_count": len(self.medicine_repo.get_expiring()),
            "recent_patients": self.patient_repo.get_recent(5),
            "low_stock_medicines": self.medicine_repo.get_low_stock()[:5],
            "expiring_medicines": self.medicine_repo.get_expiring()[:5],
            "today": date.today(),
        }
