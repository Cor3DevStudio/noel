"""Reports generation view."""

import customtkinter as ctk
from datetime import date
from tkinter import filedialog

from views.components.theme import Theme
from views.components.widgets import ActionButton, FormField, PageHeader, show_message


class ReportsView(ctk.CTkFrame):
    def __init__(self, master, report_generator, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.report_generator = report_generator
        self.grid_columnconfigure(0, weight=1)
        self._build_ui()

    def _build_ui(self) -> None:
        PageHeader(self, "Reports", "Generate and export clinic reports").grid(
            row=0, column=0, sticky="ew", pady=(0, 20)
        )

        date_frame = ctk.CTkFrame(
            self, fg_color=Theme.CARD_BG, corner_radius=Theme.CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER,
        )
        date_frame.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        date_frame.grid_columnconfigure((0, 1), weight=1)

        self.start_date = FormField(date_frame, "Start Date (YYYY-MM-DD)")
        self.start_date.set(str(date.today().replace(day=1)))
        self.start_date.grid(row=0, column=0, sticky="ew", padx=16, pady=16)
        self.end_date = FormField(date_frame, "End Date (YYYY-MM-DD)")
        self.end_date.set(str(date.today()))
        self.end_date.grid(row=0, column=1, sticky="ew", padx=16, pady=16)

        reports = [
            ("Daily Income Report", "daily_income"),
            ("Monthly Income Report", "monthly_income"),
            ("Patient Report", "patients"),
            ("Consultation Report", "consultations"),
            ("Medicine Inventory Report", "inventory"),
            ("Low Stock Report", "low_stock"),
            ("Expiring Medicine Report", "expiring"),
            ("Billing Report", "billing"),
            ("PhilHealth Report", "philhealth"),
        ]

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.grid(row=2, column=0, sticky="nsew")
        grid.grid_columnconfigure((0, 1, 2), weight=1)

        for i, (title, key) in enumerate(reports):
            card = ctk.CTkFrame(
                grid, fg_color=Theme.CARD_BG, corner_radius=Theme.CORNER_RADIUS,
                border_width=1, border_color=Theme.BORDER,
            )
            card.grid(row=i // 3, column=i % 3, sticky="nsew", padx=8, pady=8)
            ctk.CTkLabel(card, text=title, font=Theme.FONT_SUBHEADING, text_color=Theme.TEXT_PRIMARY).pack(
                padx=16, pady=(16, 12)
            )
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(padx=16, pady=(0, 16))
            ActionButton(btn_frame, text="PDF", width=80, command=lambda k=key: self._export(k, "pdf")).pack(side="left", padx=4)
            ActionButton(btn_frame, text="Excel", width=80, style="secondary", command=lambda k=key: self._export(k, "excel")).pack(side="left", padx=4)

    def _export(self, report_type: str, fmt: str) -> None:
        ext = ".pdf" if fmt == "pdf" else ".xlsx"
        filetypes = [("PDF files", "*.pdf")] if fmt == "pdf" else [("Excel files", "*.xlsx")]
        path = filedialog.asksaveasfilename(defaultextension=ext, filetypes=filetypes)
        if not path:
            return
        ok, msg = self.report_generator.generate(
            report_type, fmt, path,
            self.start_date.get(), self.end_date.get(),
        )
        show_message(self, "Reports", msg, "success" if ok else "error")
