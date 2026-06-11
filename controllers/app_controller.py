"""Application controllers - bridge between views and services."""

from typing import Any, Dict, Optional, Tuple

from sqlalchemy import text

from database.connection import SessionLocal, ensure_db_connection, init_db, _migrate_schema_if_needed
from database.seed_demo_data import seed_billing_demo
from database.seed_philhealth_rates import ensure_philhealth_rates
from services.activity_service import ActivityService
from services.appointment_service import AppointmentService
from services.auth_service import AuthService
from services.billing_service import BillingService
from services.consultation_service import ConsultationService
from services.dashboard_service import DashboardService
from services.inventory_service import InventoryService
from services.patient_service import PatientService
from services.philhealth_service import PhilHealthService
from services.settings_service import SettingsService


class AppController:
    """Central controller managing database sessions and services."""

    def __init__(self) -> None:
        self.session = SessionLocal()
        self._reports = None
        self._init_services()

    def _init_services(self) -> None:
        self.activity = ActivityService(self.session)
        self.auth = AuthService(self.session, activity_service=self.activity)
        self.patients = PatientService(self.session, activity_service=self.activity)
        self.appointments = AppointmentService(self.session, activity_service=self.activity)
        self.consultations = ConsultationService(self.session, activity_service=self.activity)
        self.inventory = InventoryService(self.session, activity_service=self.activity)
        self.billing = BillingService(self.session, activity_service=self.activity)
        self.philhealth = PhilHealthService(self.session, activity_service=self.activity)
        self.dashboard = DashboardService(self.session)
        self.settings = SettingsService(self.session, activity_service=self.activity)

    @property
    def reports(self):
        """Lazy-load ReportLab/OpenPyXL report generator on first use."""
        if self._reports is None:
            from reports.report_generator import ReportGenerator

            self._reports = ReportGenerator(
                self.session,
                settings_service=self.settings,
                activity_service=self.activity,
            )
        return self._reports

    def ensure_database(self) -> None:
        """Verify MySQL, create tables, migrate schema, and seed missing defaults."""
        ensure_db_connection()
        init_db(run_migrations=True)
        self.session.execute(text("SELECT 1"))
        self._ensure_startup_data()

    def _ensure_startup_data(self) -> None:
        """Idempotent seed for roles, accounts, rates, and demo billing showcase."""
        self.auth.initialize_roles()
        self.auth.create_seed_accounts()
        self.settings.get_settings()
        ensure_philhealth_rates(self.session)
        seed_billing_demo(self.session)
        self.session.commit()

    def initialize_database(self) -> None:
        """Full database initialization (create DB, tables + startup data)."""
        self.ensure_database()

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

    def log_page_open(self, page_key: str, page_title: str) -> None:
        self.activity.log_page_open(page_key, page_title)

    def commit(self) -> None:
        self.session.commit()

    def close(self) -> None:
        if self.session:
            self.session.close()
