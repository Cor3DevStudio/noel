"""Main application shell with sidebar navigation."""

from datetime import datetime

import customtkinter as ctk

from config.settings import APP_NAME
from utils.security import session_manager
from views.components.theme import Theme


class MainAppView(ctk.CTkFrame):
    NAV_ITEMS = [
        ("dashboard",     "Dashboard",     "⊞"),
        ("patients",      "Patients",      "◉"),
        ("appointments",  "Appointments",  "⊟"),
        ("consultations", "Consultations", "⊕"),
        ("inventory",     "Inventory",     "≡"),
        ("billing",       "Billing",       "◈"),
        ("philhealth",    "PhilHealth",    "⊗"),
        ("pricelist",     "Price List",    "₱"),
        ("reports",       "Reports",       "☰"),
        ("settings",      "Settings",      "⊙"),
    ]

    # Sidebar palette — all monochrome
    _SBG      = "#0D1117"   # sidebar background
    _SHOV     = "#161B22"   # hover background
    _SACT     = "#1C2128"   # active background
    _SACC     = "#3B82F6"   # left-bar accent (active indicator)
    _SDIV     = "#21262D"   # divider lines
    _STXT     = "#E6EDF3"   # primary text (active)
    _SMUT     = "#8B949E"   # secondary text (inactive)
    _SDIM     = "#484F58"   # very muted text (labels)
    _SAVATAR  = "#21262D"   # avatar background
    _SBADGE   = "#161B22"   # logo badge background

    def __init__(self, master, on_logout, on_page_open=None, **kwargs):
        super().__init__(master, fg_color=Theme.PAGE_BG, **kwargs)
        self.on_logout = on_logout
        self.on_page_open = on_page_open
        self._active_page_key: str | None = None
        self.views: dict = {}
        self.nav_buttons: dict = {}
        self.nav_indicators: dict = {}
        self.current_view = None
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_sidebar()
        self._build_topbar()
        self._build_content()

    def register_views(self, views: dict) -> None:
        self.views = views
        default = next(
            (k for k, _, _ in self.NAV_ITEMS if k in self.nav_buttons),
            next(iter(self.nav_buttons), None),
        )
        if default:
            self.show_view(default)

    # ------------------------------------------------------------------ sidebar
    def _build_sidebar(self) -> None:
        self.sidebar = ctk.CTkFrame(
            self, fg_color=self._SBG, width=240, corner_radius=0
        )
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_propagate(False)

        self._sidebar_brand()
        self._sidebar_divider(pady=(0, 16))
        self._sidebar_nav()
        self._sidebar_profile_card()

    def _sidebar_brand(self) -> None:
        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=20, pady=(28, 0))

        row = ctk.CTkFrame(brand, fg_color="transparent")
        row.pack(fill="x")

        badge = ctk.CTkFrame(
            row, fg_color=self._SBADGE, width=36, height=36, corner_radius=8
        )
        badge.pack(side="left")
        badge.pack_propagate(False)
        ctk.CTkLabel(
            badge, text="H",
            font=("Segoe UI", 15, "bold"),
            text_color=self._STXT,
        ).place(relx=0.5, rely=0.5, anchor="center")

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", padx=(12, 0))
        ctk.CTkLabel(
            info, text="Hospital CMS",
            font=("Segoe UI", 13, "bold"),
            text_color=self._STXT, anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            info, text="Admin Panel",
            font=("Segoe UI", 10),
            text_color=self._SDIM, anchor="w",
        ).pack(anchor="w")

    def _sidebar_user(self) -> None:
        pass  # replaced by _sidebar_profile_card

    def _sidebar_nav(self) -> None:
        ctk.CTkLabel(
            self.sidebar, text="MENU",
            font=("Segoe UI", 9, "bold"),
            text_color=self._SDIM, anchor="w",
        ).pack(fill="x", padx=24, pady=(0, 6))

        self.nav_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.nav_container.pack(fill="both", expand=True, padx=8)

        for key, label, icon in self.NAV_ITEMS:
            if not session_manager.has_permission(key):
                continue
            self._create_nav_item(key, label, icon)

    def _create_nav_item(self, key: str, label: str, icon: str) -> None:
        row = ctk.CTkFrame(self.nav_container, fg_color="transparent", height=40)
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)

        # left-bar accent indicator — fixed width, fills locked row height
        indicator = ctk.CTkFrame(row, fg_color="transparent", width=3, corner_radius=2)
        indicator.pack(side="left", fill="y")

        btn = ctk.CTkButton(
            row,
            text=f"  {icon}   {label}",
            anchor="w",
            height=40,
            font=("Segoe UI", 12),
            fg_color="transparent",
            text_color=self._SMUT,
            hover_color=self._SHOV,
            corner_radius=8,
            command=lambda k=key: self.show_view(k),
        )
        btn.pack(side="left", fill="both", expand=True)

        self.nav_buttons[key] = btn
        self.nav_indicators[key] = indicator

    def _sidebar_signout(self) -> None:
        pass  # replaced by _sidebar_profile_card

    def _sidebar_profile_card(self) -> None:
        """Bottom profile card: avatar + name + role + sign out button."""
        user = session_manager.get_current_user()
        if not user:
            return

        # ── thin divider ─────────────────────────────────────────────────────
        ctk.CTkFrame(
            self.sidebar, fg_color=self._SDIV, height=1
        ).pack(fill="x", padx=0, pady=(0, 0))

        # ── profile card container ────────────────────────────────────────────
        card = ctk.CTkFrame(
            self.sidebar,
            fg_color=self._SHOV,
            corner_radius=0,
        )
        card.pack(fill="x", pady=0)

        # ── user row ──────────────────────────────────────────────────────────
        user_row = ctk.CTkFrame(card, fg_color="transparent")
        user_row.pack(fill="x", padx=16, pady=(14, 10))

        # Avatar circle — role-based color
        role_colors = {
            "Administrator": "#2D6A4F",
            "Doctor":        "#1A5276",
            "Receptionist":  "#6E2F8A",
            "Cashier":       "#7D4E00",
        }
        avatar_color = role_colors.get(user["role"], "#2D4A7A")
        initials = "".join(p[0].upper() for p in user["full_name"].split()[:2])

        avatar = ctk.CTkFrame(
            user_row, fg_color=avatar_color,
            width=40, height=40, corner_radius=20,
        )
        avatar.pack(side="left")
        avatar.pack_propagate(False)
        ctk.CTkLabel(
            avatar, text=initials,
            font=("Segoe UI", 13, "bold"),
            text_color="white",
        ).place(relx=0.5, rely=0.5, anchor="center")

        # Name + role
        meta = ctk.CTkFrame(user_row, fg_color="transparent")
        meta.pack(side="left", padx=(10, 0), fill="x", expand=True)

        ctk.CTkLabel(
            meta, text=user["full_name"],
            font=("Segoe UI", 12, "bold"),
            text_color=self._STXT, anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            meta, text=user["role"],
            font=("Segoe UI", 10),
            text_color=self._SDIM, anchor="w",
        ).pack(anchor="w")

        # ── Sign Out button ────────────────────────────────────────────────────
        ctk.CTkFrame(card, fg_color=self._SDIV, height=1).pack(fill="x", padx=16)

        sign_out_row = ctk.CTkFrame(card, fg_color="transparent", height=40)
        sign_out_row.pack(fill="x", pady=(4, 12))
        sign_out_row.pack_propagate(False)

        ctk.CTkButton(
            sign_out_row,
            text="  ⊣  Sign out",
            anchor="w",
            height=36,
            font=("Segoe UI", 12),
            fg_color="transparent",
            text_color="#8B949E",
            hover_color="#2A1010",
            corner_radius=8,
            command=self.on_logout,
        ).pack(fill="x", padx=10, pady=2)

    def _sidebar_divider(self, pady=(0, 0)) -> None:
        ctk.CTkFrame(
            self.sidebar, fg_color=self._SDIV, height=1
        ).pack(fill="x", padx=20, pady=pady)

    # ------------------------------------------------------------------ topbar
    def _build_topbar(self) -> None:
        self.topbar = ctk.CTkFrame(
            self, fg_color=Theme.PRIMARY, height=60, corner_radius=0
        )
        self.topbar.grid(row=0, column=1, sticky="new")
        self.topbar.grid_propagate(False)
        self.topbar.grid_columnconfigure(0, weight=1)

        left = ctk.CTkFrame(self.topbar, fg_color="transparent")
        left.pack(side="left", fill="y", padx=28, pady=16)
        self.page_title = ctk.CTkLabel(
            left, text="Dashboard",
            font=Theme.FONT_HEADING, text_color=Theme.TEXT_PRIMARY, anchor="w",
        )
        self.page_title.pack(anchor="w")
        self.page_subtitle = ctk.CTkLabel(
            left, text="Overview of clinic operations",
            font=Theme.FONT_SMALL, text_color=Theme.TEXT_SECONDARY, anchor="w",
        )
        self.page_subtitle.pack(anchor="w", pady=(2, 0))

        right = ctk.CTkFrame(self.topbar, fg_color="transparent")
        right.pack(side="right", padx=28, pady=10)

        self._clock_label = ctk.CTkLabel(
            right,
            text="",
            font=("Segoe UI", 22, "bold"),
            text_color=Theme.TEXT_PRIMARY,
            anchor="e",
        )
        self._clock_label.pack(anchor="e")

        self._date_label = ctk.CTkLabel(
            right,
            text="",
            font=Theme.FONT_TINY,
            text_color=Theme.TEXT_SECONDARY,
            anchor="e",
        )
        self._date_label.pack(anchor="e", pady=(2, 0))

        self._tick()

    def _tick(self) -> None:
        now = datetime.now()
        self._clock_label.configure(text=now.strftime("%I:%M:%S %p"))
        self._date_label.configure(text=now.strftime("%A, %B %d, %Y"))
        self.after(1000, self._tick)

    # ----------------------------------------------------------------- content
    def _build_content(self) -> None:
        self.content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.content.grid(row=1, column=1, sticky="nsew", padx=(16, 20), pady=(12, 16))
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

    # ---------------------------------------------------------------- routing
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
            "dashboard":     ("Dashboard",     "Overview of clinic operations"),
            "patients":      ("Patients",       "Manage patient records"),
            "appointments":  ("Appointments",   "Schedule and track visits"),
            "consultations": ("Consultations",  "Medical records and notes"),
            "inventory":     ("Inventory",      "Medicine stock management"),
            "billing":       ("Billing",        "Payments and receipts"),
            "philhealth":    ("PhilHealth",     "Benefit computation"),
            "pricelist":     ("Price List",     "Browse & edit PhilHealth case rates"),
            "reports":       ("Reports",        "Export clinic reports"),
            "settings":      ("Settings",       "System configuration"),
        }
        title, subtitle = titles.get(key, (key.replace("_", " ").title(), ""))
        self.page_title.configure(text=title)
        self.page_subtitle.configure(text=subtitle)

        if self.on_page_open and key != self._active_page_key:
            self.on_page_open(key, title)
        self._active_page_key = key

        for nav_key, btn in self.nav_buttons.items():
            ind = self.nav_indicators.get(nav_key)
            if nav_key == key:
                btn.configure(fg_color=self._SACT, text_color=self._STXT)
                if ind:
                    ind.configure(fg_color=self._SACC)
            else:
                btn.configure(fg_color="transparent", text_color=self._SMUT)
                if ind:
                    ind.configure(fg_color="transparent")

        if hasattr(view, "refresh"):
            view.refresh()
