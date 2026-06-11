"""Billing and payment view."""

import customtkinter as ctk
from decimal import Decimal

from utils.helpers import format_currency
from views.components.theme import Theme
from views.components.widgets import ActionButton, DataTable, FormField, PageHeader, show_message


class BillingView(ctk.CTkFrame):
    def __init__(self, master, billing_service, patient_service, settings_service, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.billing_service = billing_service
        self.patient_service = patient_service
        self.settings_service = settings_service
        self.current_billing = None
        self.items: list = []
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self._build_ui()

    def _build_ui(self) -> None:
        PageHeader(self, "Billing", "Process payments and generate receipts").grid(
            row=0, column=0, sticky="ew", pady=(0, 16)
        )

        top = ctk.CTkFrame(
            self, fg_color=Theme.CARD_BG, corner_radius=Theme.CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER,
        )
        top.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        top.grid_columnconfigure((0, 1, 2, 3), weight=1)

        patients = [f"{p.id} - {p.full_name}" for p in self.patient_service.search("")]
        self.patient_field = FormField(top, "Patient", "combo", patients or ["No patients"])
        self.patient_field.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        self.item_desc = FormField(top, "Item Description")
        self.item_desc.grid(row=0, column=1, sticky="ew", padx=12, pady=12)
        self.item_price = FormField(top, "Unit Price")
        self.item_price.grid(row=0, column=2, sticky="ew", padx=12, pady=12)
        self.item_qty = FormField(top, "Quantity")
        self.item_qty.set("1")
        self.item_qty.grid(row=0, column=3, sticky="ew", padx=12, pady=12)

        btn_row = ctk.CTkFrame(top, fg_color="transparent")
        btn_row.grid(row=1, column=0, columnspan=4, sticky="w", padx=12, pady=(0, 12))
        ActionButton(btn_row, text="Add Consultation Fee", command=self._add_consultation_fee).pack(side="left", padx=(0, 8))
        ActionButton(btn_row, text="Add Item", command=self._add_item).pack(side="left", padx=(0, 8))
        ActionButton(btn_row, text="Create Bill", command=self._create_bill).pack(side="left", padx=(0, 8))

        self.items_table = DataTable(self, ["Description", "Qty", "Unit Price", "Total"])
        self.items_table.grid(row=2, column=0, sticky="ew", pady=(0, 12))

        bottom = ctk.CTkFrame(
            self, fg_color=Theme.CARD_BG, corner_radius=Theme.CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER,
        )
        bottom.grid(row=3, column=0, sticky="nsew")
        bottom.grid_columnconfigure((0, 1, 2), weight=1)

        self.total_label = ctk.CTkLabel(bottom, text="Total: ₱0.00", font=Theme.FONT_HEADING, text_color=Theme.ACCENT)
        self.total_label.grid(row=0, column=0, padx=20, pady=20, sticky="w")

        self.payment_amount = FormField(bottom, "Payment Amount")
        self.payment_amount.grid(row=0, column=1, sticky="ew", padx=12, pady=12)
        self.payment_method = FormField(bottom, "Payment Method", "combo", ["Cash", "Check", "Bank Transfer", "GCash", "Other"])
        self.payment_method.grid(row=0, column=2, sticky="ew", padx=12, pady=12)

        ActionButton(bottom, text="Record Payment", style="success", command=self._record_payment).grid(
            row=1, column=1, pady=(0, 20)
        )

        self.history_table = DataTable(self, ["Bill No.", "Patient", "Total", "Paid", "Balance", "Status"])
        self.history_table.grid(row=4, column=0, sticky="nsew", pady=(12, 0))
        self.rowconfigure(4, weight=1)

    def _parse_patient_id(self) -> int | None:
        try:
            return int(self.patient_field.get().split(" - ")[0])
        except (ValueError, IndexError):
            return None

    def _add_consultation_fee(self) -> None:
        settings = self.settings_service.get_settings()
        fee = float(settings.consultation_fee)
        self.items.append({
            "item_type": "Consultation",
            "description": "Consultation Fee",
            "quantity": 1,
            "unit_price": fee,
        })
        self._refresh_items()

    def _add_item(self) -> None:
        desc = self.item_desc.get()
        if not desc:
            show_message(self, "Validation", "Enter item description.", "warning")
            return
        try:
            price = float(self.item_price.get() or 0)
            qty = int(self.item_qty.get() or 1)
        except ValueError:
            show_message(self, "Validation", "Invalid price or quantity.", "warning")
            return
        self.items.append({
            "item_type": "Other",
            "description": desc,
            "quantity": qty,
            "unit_price": price,
        })
        self._refresh_items()

    def _refresh_items(self) -> None:
        self.items_table.clear_rows()
        total = Decimal("0")
        for item in self.items:
            line_total = Decimal(str(item["unit_price"])) * item["quantity"]
            total += line_total
            self.items_table.add_row([
                item["description"], item["quantity"],
                format_currency(item["unit_price"]), format_currency(line_total),
            ])
        self.total_label.configure(text=f"Total: {format_currency(total)}")

    def _create_bill(self) -> None:
        patient_id = self._parse_patient_id()
        if not patient_id or not self.items:
            show_message(self, "Validation", "Select patient and add items.", "warning")
            return
        ok, msg, billing = self.billing_service.create_billing(patient_id, self.items)
        show_message(self, "Billing", msg, "success" if ok else "error")
        if ok:
            self.current_billing = billing
            self._load_history(patient_id)

    def _record_payment(self) -> None:
        if not self.current_billing:
            show_message(self, "Payment", "Create a bill first.", "warning")
            return
        try:
            amount = Decimal(self.payment_amount.get())
        except Exception:
            show_message(self, "Validation", "Enter valid payment amount.", "warning")
            return
        ok, msg, payment = self.billing_service.record_payment(
            self.current_billing.id, amount, self.payment_method.get()
        )
        show_message(self, "Payment", f"{msg}\nReceipt: {payment.receipt_number if payment else ''}", "success" if ok else "error")
        if ok:
            patient_id = self._parse_patient_id()
            if patient_id:
                self._load_history(patient_id)

    def _load_history(self, patient_id: int) -> None:
        billings = self.billing_service.get_by_patient(patient_id)
        self.history_table.clear_rows()
        for b in billings:
            patient = self.patient_service.get_by_id(b.patient_id)
            name = patient.full_name if patient else "—"
            self.history_table.add_row([
                b.billing_number, name, format_currency(b.total_amount),
                format_currency(b.amount_paid), format_currency(b.balance), b.payment_status,
            ])
