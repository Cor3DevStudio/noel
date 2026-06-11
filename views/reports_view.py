"""Reports generation view — daily, monthly, yearly income and more."""

import customtkinter as ctk
from datetime import date
from tkinter import filedialog

from PIL import Image
from utils.report_icons import ensure_report_icon_path
from views.components.theme import Theme
from views.components.widgets import ActionButton, FormField, PageHeader, show_message


_REPORT_CARDS = [
    # (title, report_type, icon, description)
    ("Daily Income",       "daily_income",    "📅", "Revenue by selected date range"),
    ("Monthly Income",     "monthly_income",  "📆", "Revenue grouped by month"),
    ("Yearly Income",      "yearly_income",   "📊", "Full-year revenue summary"),
    ("Patient List",       "patients",        "👤", "All registered patients"),
    ("Consultations",      "consultations",   "🩺", "All consultation records"),
    ("Medicine Inventory", "inventory",       "💊", "Current stock levels"),
    ("Low Stock Alert",    "low_stock",       "⚠️", "Items below reorder level"),
    ("Expiring Medicines", "expiring",        "⏰", "Medicines near expiry"),
    ("Billing Summary",    "billing",         "🧾", "Billing records in range"),
    ("PhilHealth Claims",  "philhealth",      "🏥", "PhilHealth transactions"),
]


class ReportsView(ctk.CTkFrame):
    def __init__(self, master, report_generator, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.report_generator = report_generator
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._build_ui()

    def _build_ui(self) -> None:
        PageHeader(self, "Reports",
                   "Generate daily, monthly, and yearly income reports and data exports").grid(
            row=0, column=0, sticky="ew", pady=(0, 12)
        )

        # ── Date range selector ───────────────────────────────────────────
        date_frame = ctk.CTkFrame(
            self, fg_color=Theme.CARD_BG, corner_radius=Theme.CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER,
        )
        date_frame.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        date_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.start_date = FormField(date_frame, "From Date (YYYY-MM-DD)")
        self.start_date.set(str(date.today().replace(day=1)))
        self.start_date.grid(row=0, column=0, sticky="ew", padx=16, pady=16)

        self.end_date = FormField(date_frame, "To Date (YYYY-MM-DD)")
        self.end_date.set(str(date.today()))
        self.end_date.grid(row=0, column=1, sticky="ew", padx=16, pady=16)

        # Quick-select buttons
        quick = ctk.CTkFrame(date_frame, fg_color="transparent")
        quick.grid(row=0, column=2, sticky="ew", padx=16, pady=16)
        ctk.CTkLabel(quick, text="Quick select:", font=Theme.FONT_SMALL,
                     text_color=Theme.TEXT_MUTED).pack(anchor="w")
        btn_row = ctk.CTkFrame(quick, fg_color="transparent")
        btn_row.pack(fill="x", pady=(4, 0))
        for label, fn in [("Today", self._set_today), ("This Month", self._set_month),
                          ("This Year", self._set_year)]:
            ctk.CTkButton(
                btn_row, text=label, width=84, height=28,
                font=Theme.FONT_SMALL, corner_radius=8,
                fg_color=Theme.ACCENT_LIGHT, hover_color="#DBEAFE",
                text_color=Theme.ACCENT, border_width=1, border_color=Theme.BORDER,
                command=fn,
            ).pack(side="left", padx=(0, 6))

        # ── Report cards grid ─────────────────────────────────────────────
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=2, column=0, sticky="nsew")
        scroll.grid_columnconfigure((0, 1, 2), weight=1)

        for i, (title, key, _icon, desc) in enumerate(_REPORT_CARDS):
            card = ctk.CTkFrame(
                scroll, fg_color=Theme.CARD_BG, corner_radius=Theme.CORNER_RADIUS,
                border_width=1, border_color=Theme.BORDER,
            )
            card.grid(row=i // 3, column=i % 3, sticky="nsew", padx=8, pady=8)

            icon_path = ensure_report_icon_path(key, 72)
            icon_img = ctk.CTkImage(
                light_image=Image.open(icon_path),
                dark_image=Image.open(icon_path),
                size=(40, 40),
            )
            icon_lbl = ctk.CTkLabel(card, text="", image=icon_img)
            icon_lbl.pack(pady=(16, 4))
            ctk.CTkLabel(card, text=title, font=Theme.FONT_SUBHEADING,
                         text_color=Theme.TEXT_PRIMARY).pack()
            ctk.CTkLabel(card, text=desc, font=Theme.FONT_TINY,
                         text_color=Theme.TEXT_MUTED, wraplength=180).pack(pady=(2, 10))

            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(padx=16, pady=(0, 16))
            ActionButton(btn_frame, text="PDF", width=80,
                         command=lambda k=key: self._export(k, "pdf")).pack(side="left", padx=4)
            ActionButton(btn_frame, text="Excel", width=80, style="secondary",
                         command=lambda k=key: self._export(k, "excel")).pack(side="left", padx=4)

    # ── Quick-select helpers ──────────────────────────────────────────────────

    def _set_today(self) -> None:
        today = str(date.today())
        self.start_date.set(today)
        self.end_date.set(today)

    def _set_month(self) -> None:
        today = date.today()
        self.start_date.set(str(today.replace(day=1)))
        self.end_date.set(str(today))

    def _set_year(self) -> None:
        today = date.today()
        self.start_date.set(f"{today.year}-01-01")
        self.end_date.set(f"{today.year}-12-31")

    # ── Export ────────────────────────────────────────────────────────────────

    def _export(self, report_type: str, fmt: str) -> None:
        ext       = ".pdf" if fmt == "pdf" else ".xlsx"
        filetypes = [("PDF files", "*.pdf")] if fmt == "pdf" else [("Excel files", "*.xlsx")]
        name_map  = {k: t for t, k, *_ in _REPORT_CARDS}
        default   = f"{name_map.get(report_type, report_type).replace(' ', '_')}{ext}"

        path = filedialog.asksaveasfilename(
            defaultextension=ext, filetypes=filetypes, initialfile=default
        )
        if not path:
            return

        ok, msg = self.report_generator.generate(
            report_type, fmt, path,
            self.start_date.get(), self.end_date.get(),
        )
        show_message(self, "Reports", msg, "success" if ok else "error")
