"""Dashboard view with statistics widgets."""

import customtkinter as ctk

from utils.helpers import format_currency
from utils.security import session_manager
from views.components.theme import Theme
from views.components.widgets import PanelCard, QuickActionButton, StatCard


class DashboardView(ctk.CTkFrame):
    def __init__(self, master, get_stats_callback, on_navigate=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.get_stats = get_stats_callback
        self.on_navigate = on_navigate
        self.stat_cards = {}
        self.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="col")
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        user = session_manager.get_current_user()
        name = user["full_name"].split()[0] if user else "Admin"

        welcome = ctk.CTkFrame(
            self, fg_color=Theme.ACCENT, corner_radius=10, height=64,
        )
        welcome.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 12))
        welcome.grid_propagate(False)
        welcome.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            welcome, text=f"Welcome back, {name} 👋",
            font=Theme.FONT_HEADING, text_color="white", anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(10, 0))
        ctk.CTkLabel(
            welcome, text="Clinic overview for today",
            font=Theme.FONT_TINY, text_color="#BFDBFE", anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 10))

        self.monthly_badge = ctk.CTkLabel(
            welcome, text="Monthly: ₱0.00", font=Theme.FONT_SMALL,
            text_color="white", anchor="e",
        )
        self.monthly_badge.grid(row=0, column=1, rowspan=2, sticky="e", padx=20)

        # 4 essential KPIs in one compact row
        stats = [
            ("total_patients", "Patients", "👥", Theme.ACCENT, Theme.ACCENT_LIGHT),
            ("today_appointments", "Appointments", "📅", Theme.SUCCESS, Theme.SUCCESS_LIGHT),
            ("today_consultations", "Consultations", "🩺", Theme.PURPLE, Theme.PURPLE_LIGHT),
            ("today_revenue", "Revenue Today", "💰", Theme.WARNING, Theme.WARNING_LIGHT),
        ]
        for i, (key, title, icon, color, tint) in enumerate(stats):
            card = StatCard(self, title, "—", icon, color, tint, compact=True)
            card.grid(row=1, column=i, sticky="ew", padx=(0 if i == 0 else 4, 4 if i < 3 else 0), pady=(0, 12))
            self.stat_cards[key] = card

        self.recent_panel = PanelCard(self, "Recent Patients", "Latest registrations")
        self.recent_panel.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=(0, 6))
        self.recent_list = ctk.CTkFrame(self.recent_panel.body, fg_color="transparent")
        self.recent_list.pack(fill="both", expand=True)

        self.alerts_panel = PanelCard(self, "Inventory Alerts", "Stock & expiry")
        self.alerts_panel.grid(row=2, column=2, sticky="nsew", padx=6)
        self.alerts_header = ctk.CTkFrame(self.alerts_panel.body, fg_color="transparent")
        self.alerts_header.pack(fill="x", pady=(0, 6))
        self.low_stock_badge = ctk.CTkLabel(
            self.alerts_header, text="Low stock: 0", font=Theme.FONT_TINY, text_color=Theme.DANGER,
        )
        self.low_stock_badge.pack(anchor="w", pady=1)
        self.expiring_badge = ctk.CTkLabel(
            self.alerts_header, text="Expiring: 0", font=Theme.FONT_TINY, text_color=Theme.WARNING,
        )
        self.expiring_badge.pack(anchor="w", pady=1)
        self.alerts_list = ctk.CTkFrame(self.alerts_panel.body, fg_color="transparent")
        self.alerts_list.pack(fill="both", expand=True)

        actions_panel = PanelCard(self, "Quick Actions", "Common tasks")
        actions_panel.grid(row=2, column=3, sticky="nsew", padx=(6, 0))

        actions = [
            ("Register Patient", "👤", "patients"),
            ("New Appointment", "📅", "appointments"),
            ("Start Consultation", "🩺", "consultations"),
            ("Process Billing", "💳", "billing"),
        ]
        for text, icon, route in actions:
            QuickActionButton(
                actions_panel.body, text, icon, Theme.ACCENT, Theme.ACCENT_HOVER,
                command=lambda r=route: self._navigate(r),
            ).pack(fill="x", pady=3)

    def _navigate(self, route: str) -> None:
        if self.on_navigate:
            self.on_navigate(route)

    def refresh(self) -> None:
        stats = self.get_stats()
        self.stat_cards["total_patients"].set_value(str(stats.get("total_patients", 0)))
        self.stat_cards["today_appointments"].set_value(str(stats.get("today_appointments", 0)))
        self.stat_cards["today_consultations"].set_value(str(stats.get("today_consultations", 0)))
        self.stat_cards["today_revenue"].set_value(format_currency(stats.get("today_revenue", 0)))
        self.monthly_badge.configure(text=f"Monthly: {format_currency(stats.get('monthly_revenue', 0))}")
        self.low_stock_badge.configure(text=f"Low stock: {stats.get('low_stock_count', 0)}")
        self.expiring_badge.configure(text=f"Expiring: {stats.get('expiring_count', 0)}")

        for widget in self.recent_list.winfo_children():
            widget.destroy()

        recent = stats.get("recent_patients", [])[:3]
        if not recent:
            ctk.CTkLabel(
                self.recent_list, text="No patients yet.",
                font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED,
            ).pack(anchor="w", pady=4)
        else:
            for patient in recent:
                row = ctk.CTkFrame(self.recent_list, fg_color=Theme.SECONDARY, corner_radius=6, height=40)
                row.pack(fill="x", pady=2)
                row.pack_propagate(False)
                ctk.CTkLabel(
                    row, text=f"{patient.full_name}  ·  {patient.patient_number}",
                    font=Theme.FONT_SMALL, text_color=Theme.TEXT_PRIMARY, anchor="w",
                ).pack(fill="x", padx=10, pady=8)

        for widget in self.alerts_list.winfo_children():
            widget.destroy()

        low_stock = stats.get("low_stock_medicines", [])[:2]
        expiring = stats.get("expiring_medicines", [])[:2]
        if not low_stock and not expiring:
            ctk.CTkLabel(
                self.alerts_list, text="All stock levels look good ✓",
                font=Theme.FONT_SMALL, text_color=Theme.SUCCESS,
            ).pack(anchor="w", pady=4)
        else:
            for med in low_stock:
                self._alert_row(f"⚠ {med.generic_name} ({med.stock_quantity} left)", Theme.DANGER)
            for med in expiring:
                exp = med.expiration_date or "—"
                self._alert_row(f"⏰ {med.generic_name} ({exp})", Theme.WARNING)

    def _alert_row(self, text: str, color: str) -> None:
        row = ctk.CTkFrame(self.alerts_list, fg_color=Theme.SECONDARY, corner_radius=6, height=34)
        row.pack(fill="x", pady=2)
        row.pack_propagate(False)
        ctk.CTkLabel(
            row, text=text, font=Theme.FONT_TINY, text_color=color, anchor="w",
        ).pack(fill="x", padx=8, pady=6)
