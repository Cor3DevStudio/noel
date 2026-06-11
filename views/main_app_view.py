"""Main application shell with sidebar navigation."""

from datetime import datetime

import customtkinter as ctk

from config.settings import APP_NAME
from utils.security import session_manager
from views.components.theme import Theme


class MainAppView(ctk.CTkFrame):
    NAV_ITEMS = [
        ("dashboard", "Dashboard", "📊"),
        ("patients", "Patients", "👥"),
        ("appointments", "Appointments", "📅"),
        ("consultations", "Consultations", "🩺"),
        ("inventory", "Inventory", "💊"),
        ("billing", "Billing", "💰"),
        ("philhealth", "PhilHealth", "🏛️"),
        ("reports", "Reports", "📋"),
        ("settings", "Settings", "⚙️"),
    ]

    def __init__(self, master, on_logout, **kwargs):
        super().__init__(master, fg_color=Theme.PAGE_BG, **kwargs)
        self.on_logout = on_logout
        self.views: dict = {}
        self.nav_buttons = {}
        self.current_view = None
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_sidebar()
        self._build_topbar()
        self._build_content()

    def register_views(self, views: dict) -> None:
        self.views = views
        default_view = next(
            (key for key, _, _ in self.NAV_ITEMS if key in self.nav_buttons),
            next(iter(self.nav_buttons), None),
        )
        if default_view:
            self.show_view(default_view)

    def _build_sidebar(self) -> None:
        self.sidebar = ctk.CTkFrame(
            self, fg_color=Theme.SIDEBAR_BG, width=Theme.SIDEBAR_WIDTH, corner_radius=0
        )
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_propagate(False)

        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=20, pady=(28, 20))

        logo_row = ctk.CTkFrame(brand, fg_color="transparent")
        logo_row.pack(fill="x")
        logo_badge = ctk.CTkFrame(logo_row, fg_color=Theme.SIDEBAR_ACTIVE, width=40, height=40, corner_radius=10)
        logo_badge.pack(side="left")
        logo_badge.pack_propagate(False)
        ctk.CTkLabel(logo_badge, text="🏥", font=("Segoe UI Emoji", 18)).place(relx=0.5, rely=0.5, anchor="center")

        title_col = ctk.CTkFrame(logo_row, fg_color="transparent")
        title_col.pack(side="left", padx=(12, 0))
        ctk.CTkLabel(title_col, text="Clinic CMS", font=Theme.FONT_SUBHEADING, text_color="white", anchor="w").pack(anchor="w")
        ctk.CTkLabel(title_col, text="Admin Panel", font=Theme.FONT_TINY, text_color="#94A3B8", anchor="w").pack(anchor="w")

        user = session_manager.get_current_user()
        if user:
            user_card = ctk.CTkFrame(self.sidebar, fg_color=Theme.SIDEBAR_HOVER, corner_radius=12)
            user_card.pack(fill="x", padx=16, pady=(0, 16))
            ctk.CTkLabel(
                user_card, text=user["full_name"], font=Theme.FONT_BODY,
                text_color="white", anchor="w",
            ).pack(fill="x", padx=14, pady=(12, 2))
            ctk.CTkLabel(
                user_card, text=user["role"], font=Theme.FONT_TINY,
                text_color="#94A3B8", anchor="w",
            ).pack(fill="x", padx=14, pady=(0, 12))

        nav_label = ctk.CTkLabel(
            self.sidebar, text="MENU", font=Theme.FONT_TINY,
            text_color="#64748B", anchor="w",
        )
        nav_label.pack(fill="x", padx=24, pady=(0, 8))

        self.nav_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.nav_container.pack(fill="both", expand=True, padx=12)

        for key, label, icon in self.NAV_ITEMS:
            if not session_manager.has_permission(key):
                continue
            btn = ctk.CTkButton(
                self.nav_container,
                text=f"  {icon}   {label}",
                anchor="w",
                height=46,
                font=Theme.FONT_BODY,
                fg_color="transparent",
                text_color="#CBD5E1",
                hover_color=Theme.SIDEBAR_HOVER,
                corner_radius=Theme.BUTTON_RADIUS,
                command=lambda k=key: self.show_view(k),
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons[key] = btn

        ctk.CTkButton(
            self.sidebar,
            text="  🚪   Sign Out",
            anchor="w",
            height=46,
            font=Theme.FONT_BODY,
            fg_color="#334155",
            hover_color=Theme.DANGER,
            text_color="#F8FAFC",
            corner_radius=Theme.BUTTON_RADIUS,
            command=self.on_logout,
        ).pack(side="bottom", fill="x", padx=16, pady=20)

    def _build_topbar(self) -> None:
        self.topbar = ctk.CTkFrame(self, fg_color=Theme.PRIMARY, height=60, corner_radius=0)
        self.topbar.grid(row=0, column=1, sticky="new")
        self.topbar.grid_propagate(False)
        self.topbar.grid_columnconfigure(0, weight=1)

        left = ctk.CTkFrame(self.topbar, fg_color="transparent")
        left.pack(side="left", fill="y", padx=28, pady=16)
        self.page_title = ctk.CTkLabel(
            left, text="Dashboard", font=Theme.FONT_HEADING, text_color=Theme.TEXT_PRIMARY, anchor="w",
        )
        self.page_title.pack(anchor="w")
        self.page_subtitle = ctk.CTkLabel(
            left, text="Overview of clinic operations", font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_SECONDARY, anchor="w",
        )
        self.page_subtitle.pack(anchor="w", pady=(2, 0))

        right = ctk.CTkFrame(self.topbar, fg_color="transparent")
        right.pack(side="right", padx=28, pady=16)
        today = datetime.now().strftime("%A, %B %d, %Y")
        ctk.CTkLabel(
            right, text=today, font=Theme.FONT_SMALL, text_color=Theme.TEXT_SECONDARY,
        ).pack(anchor="e")

    def _build_content(self) -> None:
        self.content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.content.grid(row=1, column=1, sticky="nsew", padx=(16, 20), pady=(12, 16))
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

    def show_view(self, key: str) -> None:
        if not session_manager.has_permission(key):
            return

        if self.current_view:
            self.current_view.grid_forget()

        view = self.views.get(key)
        if not view:
            return

        view.grid(row=0, column=0, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.current_view = view

        titles = {
            "dashboard": ("Dashboard", "Overview of clinic operations"),
            "patients": ("Patients", "Manage patient records"),
            "appointments": ("Appointments", "Schedule and track visits"),
            "consultations": ("Consultations", "Medical records and notes"),
            "inventory": ("Inventory", "Medicine stock management"),
            "billing": ("Billing", "Payments and receipts"),
            "philhealth": ("PhilHealth", "Benefit computation"),
            "reports": ("Reports", "Export clinic reports"),
            "settings": ("Settings", "System configuration"),
        }
        title, subtitle = titles.get(key, (key.replace("_", " ").title(), ""))
        self.page_title.configure(text=title)
        self.page_subtitle.configure(text=subtitle)

        for nav_key, btn in self.nav_buttons.items():
            if nav_key == key:
                btn.configure(fg_color=Theme.SIDEBAR_ACTIVE, text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color="#CBD5E1")

        if hasattr(view, "refresh"):
            view.refresh()
