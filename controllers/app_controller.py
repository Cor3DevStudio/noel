"""Application controllers - bridge between views and services."""

from typing import Any, Dict, Optional, Tuple

from database.connection import SessionLocal, init_db
from services.appointment_service import AppointmentService
from services.auth_service import AuthService
from services.billing_service import BillingService
from services.consultation_service import ConsultationService
from services.dashboard_service import DashboardService
from services.inventory_service import InventoryService
from services.patient_service import PatientService
from services.philhealth_service import PhilHealthService
from services.settings_service import SettingsService
from reports.report_generator import ReportGenerator


class AppController:
    """Central controller managing database sessions and services."""

    def __init__(self) -> None:
        self.session = SessionLocal()
        self._init_services()

    def _init_services(self) -> None:
        self.auth = AuthService(self.session)
        self.patients = PatientService(self.session)
        self.appointments = AppointmentService(self.session)
        self.consultations = ConsultationService(self.session)
        self.inventory = InventoryService(self.session)
        self.billing = BillingService(self.session)
        self.philhealth = PhilHealthService(self.session)
        self.dashboard = DashboardService(self.session)
        self.settings = SettingsService(self.session)
        self.reports = ReportGenerator(self.session, settings_service=self.settings)

    def initialize_database(self) -> None:
        init_db()
        self.auth.initialize_roles()
        self.auth.create_default_admin()
        self.settings.get_settings()
        self._seed_philhealth_rates()
        self.session.commit()

    def _seed_philhealth_rates(self) -> None:
        default_rates = [
            {"case_code": "ACR001", "case_description": "Acute Gastroenteritis", "case_rate": 6000},
            {"case_code": "PN001", "case_description": "Community Acquired Pneumonia", "case_rate": 15000},
            {"case_code": "UTI001", "case_description": "Urinary Tract Infection", "case_rate": 6000},
            {"case_code": "HTN001", "case_description": "Hypertension Package", "case_rate": 9000},
            {"case_code": "DM001", "case_description": "Diabetes Mellitus Package", "case_rate": 9000},
        ]
        for rate in default_rates:
            if not self.philhealth.rate_repo.get_by_code(rate["case_code"]):
                self.philhealth.rate_repo.create(rate)

    def login(self, username: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        return self.auth.login(username, password)

    def register(self, data: dict) -> Tuple[bool, str]:
        """Create a new user account during self-registration (defaults to Doctor role)."""
        roles = self.auth.get_roles()
        default_role = next(
            (r for r in roles if r.name in ("Doctor", "Staff")),
            roles[0] if roles else None,
        )
        if default_role is None:
            return False, "No roles available. Contact the administrator."
        data["role_id"] = default_role.id
        data["is_active"] = True
        success, message, _ = self.auth.create_user(data)
        if success:
            self.session.commit()
        return success, message

    def logout(self) -> None:
        self.auth.logout()

    def get_dashboard_stats(self) -> dict:
        return self.dashboard.get_statistics()

    def commit(self) -> None:
        self.session.commit()

    def close(self) -> None:
        if self.session:
            self.session.close()
