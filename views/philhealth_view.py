"""PhilHealth benefit computation view."""

import customtkinter as ctk
from decimal import Decimal

from utils.helpers import format_currency
from views.components.theme import Theme
from views.components.widgets import ActionButton, DataTable, FormField, PageHeader, show_message


class PhilHealthView(ctk.CTkFrame):
    def __init__(self, master, philhealth_service, patient_service, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.service = philhealth_service
        self.patient_service = patient_service
        self.computation = {}
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self._build_ui()

    def _build_ui(self) -> None:
        PageHeader(self, "PhilHealth", "Benefit computation and case rates").grid(
            row=0, column=0, sticky="ew", pady=(0, 16)
        )

        form = ctk.CTkFrame(
            self, fg_color=Theme.CARD_BG, corner_radius=Theme.CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER,
        )
        form.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        form.grid_columnconfigure((0, 1, 2), weight=1)

        patients = [f"{p.id} - {p.full_name}" for p in self.patient_service.search("")]
        rates = self.service.get_case_rates()
        rate_options = [f"{r.id} - {r.case_code}: {r.case_description}" for r in rates]

        self.patient_field = FormField(form, "Patient", "combo", patients or ["No patients"])
        self.patient_field.grid(row=0, column=0, sticky="ew", padx=16, pady=16)
        self.rate_field = FormField(form, "Case Rate", "combo", rate_options or ["No case rates"])
        self.rate_field.grid(row=0, column=1, sticky="ew", padx=16, pady=16)
        self.bill_field = FormField(form, "Total Bill Amount")
        self.bill_field.set("0")
        self.bill_field.grid(row=0, column=2, sticky="ew", padx=16, pady=16)

        btn_row = ctk.CTkFrame(form, fg_color="transparent")
        btn_row.grid(row=1, column=0, columnspan=3, sticky="w", padx=16, pady=(0, 16))
        ActionButton(btn_row, text="Compute Benefits", command=self._compute).pack(side="left", padx=(0, 8))
        ActionButton(btn_row, text="Process Transaction", style="success", command=self._process).pack(side="left", padx=(0, 8))
        ActionButton(btn_row, text="View History", style="secondary", command=self._load_history).pack(side="left")

        self.summary_frame = ctk.CTkFrame(
            self, fg_color=Theme.CARD_BG, corner_radius=Theme.CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER,
        )
        self.summary_frame.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        self.summary_labels = {}
        summary_items = [
            "case_rate_amount", "hospital_share", "professional_fee",
            "philhealth_deduction", "senior_discount", "pwd_discount", "patient_balance",
        ]
        for i, key in enumerate(summary_items):
            lbl = ctk.CTkLabel(
                self.summary_frame,
                text=f"{key.replace('_', ' ').title()}: ₱0.00",
                font=Theme.FONT_BODY, text_color=Theme.TEXT_PRIMARY, anchor="w",
            )
            lbl.grid(row=i // 2, column=i % 2, sticky="w", padx=20, pady=8)
            self.summary_labels[key] = lbl

        self.history_table = DataTable(
            self, ["Date", "Case Code", "PhilHealth Deduction", "Patient Balance", "Total Bill"]
        )
        self.history_table.grid(row=3, column=0, sticky="nsew")

    def _parse_ids(self) -> tuple[int | None, int | None]:
        try:
            patient_id = int(self.patient_field.get().split(" - ")[0])
            rate_id = int(self.rate_field.get().split(" - ")[0])
            return patient_id, rate_id
        except (ValueError, IndexError):
            return None, None

    def _compute(self) -> None:
        patient_id, rate_id = self._parse_ids()
        if not patient_id or not rate_id:
            show_message(self, "Validation", "Select patient and case rate.", "warning")
            return
        try:
            total_bill = Decimal(self.bill_field.get())
        except Exception:
            show_message(self, "Validation", "Enter valid bill amount.", "warning")
            return

        self.computation = self.service.compute_benefits(patient_id, rate_id, total_bill)
        if not self.computation:
            show_message(self, "Error", "Unable to compute benefits.", "error")
            return

        for key, lbl in self.summary_labels.items():
            val = self.computation.get(key, Decimal("0"))
            lbl.configure(text=f"{key.replace('_', ' ').title()}: {format_currency(val)}")

    def _process(self) -> None:
        if not self.computation:
            self._compute()
        patient_id, rate_id = self._parse_ids()
        if not patient_id or not rate_id:
            return
        total_bill = Decimal(self.bill_field.get())
        ok, msg, _ = self.service.process_transaction(patient_id, rate_id, total_bill)
        show_message(self, "PhilHealth", msg, "success" if ok else "error")
        if ok:
            self._load_history()

    def _load_history(self) -> None:
        patient_id, _ = self._parse_ids()
        if not patient_id:
            return
        transactions = self.service.get_patient_history(patient_id)
        self.history_table.clear_rows()
        for t in transactions:
            code = t.case_rate.case_code if t.case_rate else "—"
            self.history_table.add_row([
                str(t.transaction_date)[:10], code,
                format_currency(t.philhealth_deduction),
                format_currency(t.patient_balance),
                format_currency(t.total_bill),
            ])
