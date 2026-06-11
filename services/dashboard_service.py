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
        today = date.today()
        days_elapsed = max(today.day, 1)

        monthly_revenue = self.billing_service.get_monthly_revenue()
        avg_daily_revenue = float(monthly_revenue) / days_elapsed

        low_stock = self.medicine_repo.get_low_stock()
        expiring = self.medicine_repo.get_expiring()

        return {
            # Core counts
            "total_patients":        self.patient_repo.get_active_count(),
            "today_appointments":    self.appointment_repo.count_today(),
            "today_consultations":   self.consultation_repo.count_today(),
            "monthly_consultations": self.consultation_repo.count_month(),
            "monthly_new_patients":  self.patient_repo.get_monthly_new_count(),
            # Revenue
            "today_revenue":         self.billing_service.get_today_revenue(),
            "monthly_revenue":       monthly_revenue,
            "avg_daily_revenue":     avg_daily_revenue,
            "weekly_revenue":        self.billing_service.get_weekly_revenue_data(),
            # Inventory
            "low_stock_count":       len(low_stock),
            "expiring_count":        len(expiring),
            "low_stock_medicines":   low_stock[:5],
            "expiring_medicines":    expiring[:5],
            # Meta
            "today": today,
        }
