"""Clinic Management System - Application Entry Point."""

import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import customtkinter as ctk

from config.settings import APP_NAME
from controllers.app_controller import AppController
from utils.logger import logger
from utils.security import session_manager
from views.components.theme import Theme
from views.login_view import LoginView
from views.main_app_view import MainAppView
from views.dashboard_view import DashboardView
from views.patient_view import PatientView
from views.appointment_view import AppointmentView
from views.consultation_view import ConsultationView
from views.inventory_view import InventoryView
from views.billing_view import BillingView
from views.philhealth_view import PhilHealthView
from views.pricelist_view import PriceListView
from views.reports_view import ReportsView
from views.settings_view import SettingsView
from views.components.widgets import show_message


class ClinicApplication(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1360x860")
        self.minsize(1200, 720)
        self.configure(fg_color=Theme.PAGE_BG)

        self.controller = AppController()
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=0, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.login_view = None
        self.main_view = None

        try:
            self.controller.initialize_database()
        except Exception as exc:
            logger.error("Database initialization failed: %s", exc)
            show_message(
                self, "Database Error",
                f"Could not connect to MySQL database.\n\n{exc}\n\n"
                "Please ensure MySQL is running and configure config/settings.py.\n"
                "Run database/schema.sql to create the database.",
                "error",
            )

        self.show_login()

    def show_login(self) -> None:
        if self.main_view:
            self.main_view.grid_forget()
            self.main_view.destroy()
            self.main_view = None

        self.login_view = LoginView(
            self.container,
            on_login=self.handle_login,
            on_register=self.handle_register,
        )
        self.login_view.grid(row=0, column=0, sticky="nsew")

    def handle_register(self, data: dict) -> tuple:
        return self.controller.register(data)

    def handle_login(self, username: str, password: str) -> bool:
        success, message, user_data = self.controller.login(username, password)
        if success:
            self.controller.commit()
            self._on_login_success(user_data)
            return True
        show_message(self, "Login Failed", message, "error")
        return False

    def _on_login_success(self, user_data: dict) -> None:
        if self.login_view:
            self.login_view.grid_forget()
            self.login_view.destroy()
            self.login_view = None

        ctrl = self.controller
        self.main_view = MainAppView(
            self.container,
            on_logout=self.handle_logout,
            on_page_open=self.controller.log_page_open,
        )

        content = self.main_view.content
        views = {
            "dashboard": DashboardView(
                content,
                get_stats_callback=ctrl.get_dashboard_stats,
                on_navigate=self.main_view.show_view,
            ),
            "patients": PatientView(content, patient_service=ctrl.patients),
            "appointments": AppointmentView(
                content,
                appointment_service=ctrl.appointments,
                patient_service=ctrl.patients,
                user_service=ctrl.auth,
            ),
            "consultations": ConsultationView(
                content, consultation_service=ctrl.consultations, patient_service=ctrl.patients
            ),
            "inventory": InventoryView(content, inventory_service=ctrl.inventory),
            "billing": BillingView(
                content,
                billing_service=ctrl.billing,
                patient_service=ctrl.patients,
                settings_service=ctrl.settings,
                philhealth_service=ctrl.philhealth,
            ),
            "philhealth": PhilHealthView(
                content,
                philhealth_service=ctrl.philhealth,
                patient_service=ctrl.patients,
                settings_service=ctrl.settings,
            ),
            "pricelist": PriceListView(
                content,
                philhealth_service=ctrl.philhealth,
            ),
            "reports": ReportsView(content, report_generator=ctrl.reports),
            "settings": SettingsView(
                content, settings_service=ctrl.settings, auth_service=ctrl.auth
            ),
        }
        self.main_view.register_views(views)
        self.main_view.grid(row=0, column=0, sticky="nsew")

    def handle_logout(self) -> None:
        self.controller.logout()
        self.controller.commit()
        self.show_login()

    def on_closing(self) -> None:
        self.controller.close()
        self.destroy()


def main() -> None:
    logger.info("Starting %s", APP_NAME)
    app = ClinicApplication()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
