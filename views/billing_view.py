"""Billing, SOA and payment view — dashboard design standard."""

import os
from datetime import date
from decimal import Decimal
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from config.settings import SOA_PREVIEW_DIR
from reports.pdf_generator import PDFGenerator
from utils.helpers import format_currency
from views.components.theme import Theme
from views.components.widgets import (
    ActionButton, FormField, PanelCard, SearchPickerField, show_message,
)


_STATUS_COLOR = {
    "Unpaid":    (Theme.DANGER,  Theme.DANGER_LIGHT),
    "Partial":   (Theme.WARNING, Theme.WARNING_LIGHT),
    "Paid":      (Theme.SUCCESS, Theme.SUCCESS_LIGHT),
    "Cancelled": ("#6B7280",     "#F3F4F6"),
}


# ─────────────────────────────────────────────────────────────────────────────
class _StatChip(ctk.CTkFrame):
    def __init__(self, master, label: str, color: str, tint: str, **kwargs):
        super().__init__(
            master, fg_color=tint, corner_radius=10,
            border_width=1, border_color=color, **kwargs,
        )
        self._val = ctk.CTkLabel(
            self, text="—", font=("Segoe UI", 20, "bold"), text_color=color,
        )
        self._val.pack(padx=14, pady=(10, 0), anchor="w")
        ctk.CTkLabel(
            self, text=label, font=Theme.FONT_TINY, text_color=Theme.TEXT_MUTED,
        ).pack(padx=14, pady=(0, 10), anchor="w")

    def set_value(self, v: str) -> None:
        self._val.configure(text=v)


# ─────────────────────────────────────────────────────────────────────────────
class _ContextCard(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(
            master, fg_color=Theme.CARD_BG,
            corner_radius=Theme.CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER, **kwargs,
        )
        self._bar = ctk.CTkFrame(self, fg_color=Theme.ACCENT, width=4, corner_radius=0)
        self._bar.pack(side="left", fill="y")
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(side="left", fill="both", expand=True, padx=16, pady=12)

        self._title = ctk.CTkLabel(
            body, text="No active bill",
            font=Theme.FONT_SUBHEADING, text_color=Theme.TEXT_PRIMARY, anchor="w",
        )
        self._title.pack(anchor="w")
        self._sub = ctk.CTkLabel(
            body, text="Select a patient and create or open a bill",
            font=Theme.FONT_TINY, text_color=Theme.TEXT_MUTED, anchor="w",
        )
        self._sub.pack(anchor="w")

        self._total_lbl = ctk.CTkLabel(
            body, text="", font=("Segoe UI", 22, "bold"), text_color=Theme.ACCENT, anchor="w",
        )
        self._total_lbl.pack(anchor="w", pady=(6, 0))

    def update_patient(self, patient) -> None:
        if patient is None:
            self._bar.configure(fg_color=Theme.ACCENT)
            self._title.configure(text="No patient selected")
            self._sub.configure(text="Search and select a patient to view billing history")
            self._total_lbl.configure(text="")
            return
        self._bar.configure(fg_color=Theme.ACCENT)
        self._title.configure(text=patient.full_name)
        ph = patient.philhealth_number or "No PhilHealth"
        self._sub.configure(text=f"{patient.patient_number}  ·  {ph}")
        self._total_lbl.configure(text="")

    def update_bill(self, billing, patient_name: str = "") -> None:
        if billing is None:
            self._title.configure(text="Draft — new bill")
            self._sub.configure(text="Add line items then create the bill")
            self._total_lbl.configure(text="")
            return

        status = billing.payment_status or "Unpaid"
        color, _ = _STATUS_COLOR.get(status, (Theme.ACCENT, Theme.ACCENT_LIGHT))
        self._bar.configure(fg_color=color)
        self._title.configure(text=f"Bill {billing.billing_number}")
        soa = billing.soa_number or "SOA pending"
        self._sub.configure(
            text=f"{patient_name}  ·  {soa}  ·  {status}"
        )
        self._total_lbl.configure(text=format_currency(billing.total_amount))


# ─────────────────────────────────────────────────────────────────────────────
class _BillRow(ctk.CTkFrame):
    def __init__(self, master, billing, on_select, **kwargs):
        super().__init__(
            master, fg_color="transparent", corner_radius=8,
            cursor="hand2", **kwargs,
        )
        self._billing = billing
        self._on_select = on_select
        self._selected = False

        status = billing.payment_status or "Unpaid"
        color, tint = _STATUS_COLOR.get(status, (Theme.ACCENT, Theme.ACCENT_LIGHT))

        self._bar = ctk.CTkFrame(self, fg_color="transparent", width=3, corner_radius=2)
        self._bar.pack(side="left", fill="y", padx=(4, 0))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(side="left", fill="both", expand=True, padx=(10, 12), pady=5)

        top = ctk.CTkFrame(body, fg_color="transparent")
        top.pack(fill="x")

        self._no_lbl = ctk.CTkLabel(
            top, text=billing.billing_number,
            font=("Segoe UI", 11, "bold"), text_color=Theme.TEXT_PRIMARY, anchor="w",
        )
        self._no_lbl.pack(side="left")

        badge = ctk.CTkFrame(top, fg_color=tint, corner_radius=5)
        badge.pack(side="right")
        ctk.CTkLabel(badge, text=status, font=Theme.FONT_TINY, text_color=color).pack(padx=7, pady=2)

        sub = ctk.CTkFrame(body, fg_color="transparent")
        sub.pack(fill="x")
        ctk.CTkLabel(
            sub,
            text=(
                f"Total {format_currency(billing.total_amount)}  ·  "
                f"Paid {format_currency(billing.amount_paid)}  ·  "
                f"Bal {format_currency(billing.balance)}"
            ),
            font=Theme.FONT_TINY, text_color=Theme.TEXT_SECONDARY, anchor="w",
        ).pack(side="left")

        for w in self._walk(self):
            w.bind("<Button-1>", lambda _e: self._click())
            w.bind("<Enter>", lambda _e: self._hover(True))
            w.bind("<Leave>", lambda _e: self._hover(False))

    def _walk(self, root):
        yield root
        for c in root.winfo_children():
            yield from self._walk(c)

    def _click(self) -> None:
        self._on_select(self._billing)

    def _hover(self, on: bool) -> None:
        if not self._selected:
            self.configure(fg_color=Theme.SECONDARY if on else "transparent")

    def select(self, active: bool) -> None:
        self._selected = active
        status = self._billing.payment_status or "Unpaid"
        color, _ = _STATUS_COLOR.get(status, (Theme.ACCENT, Theme.ACCENT_LIGHT))
        self.configure(fg_color=Theme.ACCENT_LIGHT if active else "transparent")
        self._bar.configure(fg_color=color if active else "transparent")
        self._no_lbl.configure(text_color=Theme.ACCENT if active else Theme.TEXT_PRIMARY)


# ─────────────────────────────────────────────────────────────────────────────
class _ItemRow(ctk.CTkFrame):
    def __init__(self, master, item: dict, **kwargs):
        super().__init__(
            master, fg_color=Theme.SECONDARY, corner_radius=8,
            border_width=1, border_color=Theme.BORDER, **kwargs,
        )
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="x", padx=12, pady=8)

        top = ctk.CTkFrame(body, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(
            top, text=item["description"],
            font=("Segoe UI", 11, "bold"), text_color=Theme.TEXT_PRIMARY, anchor="w",
        ).pack(side="left")

        line_total = Decimal(str(item["unit_price"])) * item["quantity"]
        ctk.CTkLabel(
            top, text=format_currency(line_total),
            font=("Segoe UI", 11, "bold"), text_color=Theme.ACCENT, anchor="e",
        ).pack(side="right")

        ctk.CTkLabel(
            body,
            text=(
                f"{item.get('item_type', 'Other')}  ·  "
                f"Qty {item['quantity']} × {format_currency(item['unit_price'])}"
            ),
            font=Theme.FONT_TINY, text_color=Theme.TEXT_SECONDARY, anchor="w",
        ).pack(fill="x")


# ─────────────────────────────────────────────────────────────────────────────
class BillingView(ctk.CTkFrame):
    def __init__(
        self, master, billing_service, patient_service,
        settings_service, philhealth_service=None, **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.billing_service = billing_service
        self.patient_service = patient_service
        self.settings_service = settings_service
        self.philhealth_service = philhealth_service

        self.selected_patient = None
        self.current_billing = None
        self.items: list = []
        self._bill_rows: list[_BillRow] = []

        self.grid_columnconfigure(0, weight=5)
        self.grid_columnconfigure(1, weight=7)
        self.grid_rowconfigure(0, weight=1)

        self._build_history_panel()
        self._build_workspace_panel()

    # ── Left: patient + billing history ─────────────────────────────────────
    def _build_history_panel(self) -> None:
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(3, weight=1)

        chips = ctk.CTkFrame(left, fg_color="transparent")
        chips.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        chips.grid_columnconfigure((0, 1, 2), weight=1)
        self._chip_bills  = _StatChip(chips, "Total Bills",  Theme.ACCENT,  Theme.ACCENT_LIGHT)
        self._chip_unpaid = _StatChip(chips, "Unpaid",       Theme.DANGER,  Theme.DANGER_LIGHT)
        self._chip_bal    = _StatChip(chips, "Total Balance", Theme.WARNING, Theme.WARNING_LIGHT)
        self._chip_bills.grid( row=0, column=0, sticky="ew", padx=(0, 4))
        self._chip_unpaid.grid(row=0, column=1, sticky="ew", padx=4)
        self._chip_bal.grid(   row=0, column=2, sticky="ew", padx=(4, 0))

        self._patient_picker = SearchPickerField(
            left,
            "Patient",
            label_fn=lambda p: f"{p.id} — {p.full_name} ({p.patient_number})",
            dialog_title="Select Patient",
            columns=("ID", "Name", "Patient No.", "PhilHealth"),
            row_fn=lambda p: (
                p.id, p.full_name, p.patient_number, p.philhealth_number or "—",
            ),
            search_fn=self._search_patients,
        )
        self._patient_picker.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        # Hook selection via browse dialog callback — override after pick
        orig_on_picked = self._patient_picker._on_picked

        def _on_patient_picked(item):
            orig_on_picked(item)
            self._on_patient_selected(item)

        self._patient_picker._on_picked = _on_patient_picked

        list_card = ctk.CTkFrame(
            left, fg_color=Theme.CARD_BG,
            corner_radius=Theme.CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER,
        )
        list_card.grid(row=3, column=0, sticky="nsew")
        list_card.grid_columnconfigure(0, weight=1)
        list_card.grid_rowconfigure(1, weight=1)

        hdr = ctk.CTkFrame(list_card, fg_color=Theme.SECONDARY, corner_radius=0, height=38)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)
        ctk.CTkLabel(
            hdr, text="Billing History",
            font=Theme.FONT_SUBHEADING, text_color=Theme.TEXT_PRIMARY, anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=14, pady=8)

        self._history_scroll = ctk.CTkScrollableFrame(list_card, fg_color="transparent")
        self._history_scroll.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

        toolbar = ctk.CTkFrame(left, fg_color="transparent")
        toolbar.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        ActionButton(toolbar, text="+ New Bill", command=self._new_bill).pack(side="left", padx=(0, 8))
        ActionButton(toolbar, text="Refresh", style="secondary", command=self._refresh_history).pack(side="left")

    # ── Right: bill workspace ─────────────────────────────────────────────────
    def _build_workspace_panel(self) -> None:
        self._workspace = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._workspace.grid(row=0, column=1, sticky="nsew")
        self._workspace.grid_columnconfigure(0, weight=1)

        self._context = _ContextCard(self._workspace)
        self._context.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        charges = PanelCard(
            self._workspace, "Add Charges",
            "Line items for the current bill draft",
        )
        charges.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        charges.body.grid_columnconfigure((0, 1), weight=1)

        self.item_desc = FormField(charges.body, "Item Description")
        self.item_desc.grid(row=0, column=0, columnspan=2, sticky="ew", pady=4)
        self.item_price = FormField(charges.body, "Unit Price")
        self.item_price.grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=4)
        self.item_qty = FormField(charges.body, "Quantity")
        self.item_qty.set("1")
        self.item_qty.grid(row=1, column=1, sticky="ew", padx=(6, 0), pady=4)

        charge_btns = ctk.CTkFrame(charges.body, fg_color="transparent")
        charge_btns.grid(row=2, column=0, columnspan=2, sticky="w", pady=(4, 0))
        ActionButton(charge_btns, text="Add Consultation Fee",
                     command=self._add_consultation_fee).pack(side="left", padx=(0, 8))
        ActionButton(charge_btns, text="Add Item", command=self._add_item).pack(side="left", padx=(0, 8))
        ActionButton(charge_btns, text="Create Bill", style="success",
                     command=self._create_bill).pack(side="left", padx=(0, 8))
        ActionButton(charge_btns, text="Clear Items", style="secondary",
                     command=self._clear_items).pack(side="left")

        items_panel = PanelCard(
            self._workspace, "Line Items",
            "Draft charges before billing is created",
        )
        items_panel.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        self._items_scroll = ctk.CTkScrollableFrame(items_panel.body, fg_color="transparent", height=140)
        self._items_scroll.pack(fill="x")
        self._draft_total = ctk.CTkLabel(
            items_panel.body, text="Draft Total: ₱0.00",
            font=("Segoe UI", 16, "bold"), text_color=Theme.ACCENT, anchor="e",
        )
        self._draft_total.pack(fill="x", pady=(8, 0))

        payment = PanelCard(
            self._workspace, "Payment & PhilHealth",
            "Apply benefits, record payment, and print documents",
        )
        payment.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        payment.body.grid_columnconfigure((0, 1), weight=1)

        self.ph_rate_field = SearchPickerField(
            payment.body,
            "PhilHealth Case Rate (optional)",
            label_fn=lambda r: (
                f"{r.id} - [{r.case_type}] {r.case_code}: {r.case_description[:40]}"
            ),
            dialog_title="Select PhilHealth Case Rate",
            columns=("Type", "Code", "Description", "Rate"),
            row_fn=lambda r: (
                r.case_type,
                r.case_code,
                r.case_description,
                f"₱{float(r.case_rate):,.2f}",
            ),
            search_fn=self._search_ph_rates,
            filter_options=["All", "Medical", "Surgical"],
        )
        self.ph_rate_field.grid(row=0, column=0, columnspan=2, sticky="ew", pady=4)

        self.payment_amount = FormField(payment.body, "Payment Amount")
        self.payment_amount.grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=4)
        self.payment_method = FormField(
            payment.body, "Payment Method", "combo",
            ["Cash", "Check", "Bank Transfer", "GCash", "Other"],
        )
        self.payment_method.grid(row=1, column=1, sticky="ew", padx=(6, 0), pady=4)
        self.payment_notes = FormField(payment.body, "Notes")
        self.payment_notes.grid(row=2, column=0, columnspan=2, sticky="ew", pady=4)

        pay_btns = ctk.CTkFrame(payment.body, fg_color="transparent")
        pay_btns.grid(row=3, column=0, columnspan=2, sticky="w", pady=(4, 0))
        ActionButton(pay_btns, text="Apply PhilHealth & Pay", style="success",
                     command=self._apply_ph_and_pay).pack(side="left", padx=(0, 8))
        ActionButton(pay_btns, text="Record Payment",
                     command=self._record_payment).pack(side="left", padx=(0, 8))
        ActionButton(pay_btns, text="Preview SOA", style="secondary",
                     command=self._preview_soa).pack(side="left", padx=(0, 8))
        ActionButton(pay_btns, text="Print SOA", style="secondary",
                     command=self._print_soa).pack(side="left", padx=(0, 8))
        ActionButton(pay_btns, text="Attach XML to eClaims", style="secondary",
                     command=self._attach_soa_xml_to_eclaims).pack(side="left", padx=(0, 8))
        ActionButton(pay_btns, text="Print Receipt", style="secondary",
                     command=self._print_receipt).pack(side="left")

    # ── Patient / history ─────────────────────────────────────────────────────
    def _search_patients(self, query: str, _filter: str, page: int, per_page: int):
        patients = self.patient_service.search(query)
        total = len(patients)
        start = (page - 1) * per_page
        return patients[start:start + per_page], total

    def _on_patient_selected(self, patient) -> None:
        self.selected_patient = patient
        self.current_billing = None
        self.items = []
        self._refresh_items()
        self._context.update_patient(patient)
        self._context.update_bill(None)
        self._refresh_history()

    def _refresh_history(self) -> None:
        for w in self._history_scroll.winfo_children():
            w.destroy()
        self._bill_rows.clear()

        if not self.selected_patient:
            self._chip_bills.set_value("—")
            self._chip_unpaid.set_value("—")
            self._chip_bal.set_value("—")
            ctk.CTkLabel(
                self._history_scroll, text="Select a patient to view billing history.",
                font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED,
            ).pack(pady=20)
            return

        billings = self.billing_service.get_by_patient(self.selected_patient.id)
        unpaid = sum(1 for b in billings if (b.payment_status or "") != "Paid")
        balance = sum(Decimal(str(b.balance or 0)) for b in billings)

        self._chip_bills.set_value(str(len(billings)))
        self._chip_unpaid.set_value(str(unpaid))
        self._chip_bal.set_value(format_currency(balance))

        if not billings:
            ctk.CTkLabel(
                self._history_scroll, text="No bills yet for this patient.",
                font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED,
            ).pack(pady=20)
            return

        for b in billings:
            row = _BillRow(self._history_scroll, b, on_select=self._select_bill)
            row.pack(fill="x", padx=2)
            ctk.CTkFrame(self._history_scroll, fg_color=Theme.BORDER, height=1).pack(fill="x", padx=6)
            self._bill_rows.append(row)

        if self.current_billing:
            for rw in self._bill_rows:
                if rw._billing.id == self.current_billing.id:
                    rw.select(True)
                    break

    def _select_bill(self, billing) -> None:
        self.current_billing = billing
        for rw in self._bill_rows:
            rw.select(rw._billing.id == billing.id)
        name = self.selected_patient.full_name if self.selected_patient else ""
        self._context.update_bill(billing, name)

    def _new_bill(self) -> None:
        if not self.selected_patient:
            show_message(self, "Billing", "Select a patient first.", "warning")
            return
        self.current_billing = None
        self.items = []
        self._refresh_items()
        self._context.update_bill(None)
        for rw in self._bill_rows:
            rw.select(False)

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _search_ph_rates(self, query: str, case_type: str, page: int, per_page: int):
        if not self.philhealth_service:
            return [], 0
        return self.philhealth_service.search_rates(query, case_type, page, per_page)

    def _parse_patient_id(self) -> int | None:
        if self.selected_patient:
            return self.selected_patient.id
        item = self._patient_picker.get_item()
        return item.id if item else None

    def _get_selected_ph_rate(self):
        return self.ph_rate_field.get_item()

    def _add_consultation_fee(self) -> None:
        settings = self.settings_service.get_settings()
        fee = float(settings.consultation_fee)
        self.items.append({
            "item_type": "Consultation",
            "description": "Consultation Fee",
            "quantity": 1,
            "unit_price": fee,
            "price_as_of": settings.consultation_fee_effective_date or date.today(),
        })
        self._refresh_items()
        self._context.update_bill(None)

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
            "price_as_of": date.today(),
        })
        self.item_desc.set("")
        self._refresh_items()
        self._context.update_bill(None)

    def _clear_items(self) -> None:
        self.items = []
        self.current_billing = None
        self._refresh_items()
        if self.selected_patient:
            self._context.update_patient(self.selected_patient)
        self._context.update_bill(None)
        for rw in self._bill_rows:
            rw.select(False)

    def _refresh_items(self) -> None:
        for w in self._items_scroll.winfo_children():
            w.destroy()

        total = Decimal("0")
        if not self.items:
            ctk.CTkLabel(
                self._items_scroll, text="No line items yet.",
                font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED,
            ).pack(pady=12)
        else:
            for item in self.items:
                _ItemRow(self._items_scroll, item).pack(fill="x", pady=3)
                total += Decimal(str(item["unit_price"])) * item["quantity"]

        self._draft_total.configure(text=f"Draft Total: {format_currency(total)}")

    # ── Actions ───────────────────────────────────────────────────────────────
    def _create_bill(self) -> None:
        patient_id = self._parse_patient_id()
        if not patient_id or not self.items:
            show_message(self, "Validation", "Select patient and add items.", "warning")
            return
        ok, msg, billing = self.billing_service.create_billing(patient_id, self.items)
        show_message(self, "Billing", msg, "success" if ok else "error")
        if ok:
            self.current_billing = billing
            self.items = []
            self._refresh_items()
            self._refresh_history()
            name = self.selected_patient.full_name if self.selected_patient else ""
            self._context.update_bill(billing, name)

    def _apply_ph_and_pay(self) -> None:
        if not self.current_billing:
            show_message(self, "Payment", "Create or select a bill first.", "warning")
            return

        rate = self._get_selected_ph_rate()
        if rate:
            deduction = Decimal(str(rate.health_facility_fee or rate.case_rate * Decimal("0.70")))
            ok, msg = self.billing_service.set_philhealth_case_rate(
                self.current_billing.id, rate.id, deduction,
            )
            if not ok:
                show_message(self, "PhilHealth", msg, "error")
                return
            self.current_billing = self.billing_service.get_by_id(self.current_billing.id)

        self._record_payment()

    def _record_payment(self) -> None:
        if not self.current_billing:
            show_message(self, "Payment", "Create or select a bill first.", "warning")
            return
        try:
            amount = Decimal(self.payment_amount.get())
        except Exception:
            show_message(self, "Validation", "Enter valid payment amount.", "warning")
            return
        ok, msg, payment = self.billing_service.record_payment(
            self.current_billing.id, amount, self.payment_method.get(),
            self.payment_notes.get(),
        )
        receipt_no = payment.receipt_number if payment else ""
        show_message(
            self, "Payment",
            f"{msg}\nReceipt: {receipt_no}" if receipt_no else msg,
            "success" if ok else "error",
        )
        if ok:
            self.current_billing = self.billing_service.get_by_id(self.current_billing.id)
            self._refresh_history()
            name = self.selected_patient.full_name if self.selected_patient else ""
            self._context.update_bill(self.current_billing, name)

    # ── Printing ──────────────────────────────────────────────────────────────
    def _get_clinic_info(self) -> dict:
        s = self.settings_service.get_settings() if self.settings_service else None
        return {
            "clinic_name": (s.clinic_name if s else "Clinic") or "Clinic",
            "clinic_address": (s.clinic_address if s else "") or "",
            "philhealth_accreditation": (s.philhealth_accreditation if s else "") or "",
            "header": (s.receipt_header if s else "") or "",
            "footer": (s.receipt_footer if s else "") or "",
        }

    def _load_soa_context(self) -> dict | None:
        if not self.current_billing:
            show_message(self, "SOA", "Select or create a bill first.", "warning")
            return None
        soa_data = self.billing_service.get_soa_data(self.current_billing.id)
        if not soa_data:
            show_message(self, "SOA", "Could not load billing data.", "error")
            return None
        return {
            **soa_data,
            "info": self._get_clinic_info(),
        }

    def _write_soa_pdf(self, path: str, ctx: dict, *, soa_number: str) -> None:
        billing = ctx["billing"]
        patient = ctx["patient"]
        ph = ctx.get("philhealth") or {}
        info = ctx["info"]
        PDFGenerator.generate_soa(
            output_path=path,
            clinic_name=info["clinic_name"],
            clinic_address=info["clinic_address"],
            soa_number=soa_number,
            billing_number=billing.billing_number,
            patient_name=patient.full_name,
            philhealth_number=patient.philhealth_number or "—",
            admission_date=str(billing.created_at.date()),
            discharge_date=str(date.today()),
            items=ctx["items"],
            subtotal=float(billing.subtotal),
            discount_amount=float(billing.discount_amount),
            discount_type=billing.discount_type or "",
            philhealth_deduction=float(billing.philhealth_deduction),
            total_amount=float(billing.total_amount),
            amount_paid=float(billing.amount_paid),
            balance=float(billing.balance),
            case_code=ph.get("case_code", ""),
            case_description=ph.get("case_description", ""),
            case_type=ph.get("case_type", ""),
            case_rate=ph.get("case_rate", 0),
            health_facility_fee=ph.get("health_facility_fee", 0),
            professional_fee_ph=ph.get("professional_fee_ph", 0),
            ph_effective_date=ph.get("effective_date"),
            header=info["header"],
            footer=info["footer"],
            accreditation_no=info.get("philhealth_accreditation", ""),
            member_type=patient.philhealth_member_type or patient.philhealth_category or "",
        )

    def _preview_soa(self) -> None:
        ctx = self._load_soa_context()
        if not ctx:
            return

        billing = ctx["billing"]
        patient = ctx["patient"]
        preview_number = billing.soa_number or ctx.get("soa_number") or "PREVIEW"
        safe_name = "".join(c if c.isalnum() else "_" for c in patient.last_name)[:24] or "patient"
        path = SOA_PREVIEW_DIR / f"SOA_preview_{safe_name}_{billing.billing_number}.pdf"

        try:
            self._write_soa_pdf(str(path), ctx, soa_number=preview_number)
            os.startfile(str(path))
        except Exception as exc:
            show_message(self, "SOA Preview", str(exc), "error")

    def _print_soa(self) -> None:
        ctx = self._load_soa_context()
        if not ctx:
            return

        billing = ctx["billing"]
        patient = ctx["patient"]

        self.billing_service.assign_soa_number(billing.id)
        self.billing_service.session.commit()
        billing = self.billing_service.get_by_id(billing.id)
        ctx["billing"] = billing
        self.current_billing = billing

        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")],
            initialfile=f"SOA_{patient.last_name}_{billing.billing_number}.pdf",
        )
        if not path:
            return

        try:
            self._write_soa_pdf(path, ctx, soa_number=billing.soa_number or "—")
            show_message(self, "SOA", "Statement of Account saved.", "success")
            os.startfile(path)
            name = self.selected_patient.full_name if self.selected_patient else ""
            self._context.update_bill(billing, name)
            self._refresh_history()
        except Exception as exc:
            show_message(self, "SOA Error", str(exc), "error")

    def _attach_soa_xml_to_eclaims(self) -> None:
        if not self.current_billing:
            show_message(self, "SOA XML", "Select or create a bill first.", "warning")
            return
        if not self.philhealth_service:
            show_message(self, "SOA XML", "PhilHealth service is not available.", "error")
            return

        info = self._get_clinic_info()
        ok, msg, _ = self.billing_service.attach_soa_xml_to_eclaims(
            self.current_billing.id,
            self.philhealth_service,
            info,
        )
        if ok:
            self.philhealth_service.session.commit()
            self.current_billing = self.billing_service.get_by_id(self.current_billing.id)
        show_message(self, "SOA XML → eClaims", msg, "success" if ok else "error")

    def _print_receipt(self) -> None:
        if not self.current_billing:
            show_message(self, "Receipt", "Select or create a bill first.", "warning")
            return

        soa_data = self.billing_service.get_soa_data(self.current_billing.id)
        if not soa_data:
            return
        billing = soa_data["billing"]
        patient = soa_data["patient"]
        info = self._get_clinic_info()

        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")],
            initialfile=f"Receipt_{patient.last_name}_{billing.billing_number}.pdf",
        )
        if not path:
            return
        try:
            PDFGenerator.generate_receipt(
                output_path=path,
                clinic_name=info["clinic_name"],
                clinic_address=info["clinic_address"],
                receipt_number=billing.billing_number,
                patient_name=patient.full_name,
                items=soa_data["items"],
                subtotal=float(billing.subtotal),
                discount=float(billing.discount_amount),
                philhealth_deduction=float(billing.philhealth_deduction),
                total=float(billing.total_amount),
                amount_paid=float(billing.amount_paid),
                header=info["header"],
                footer=info["footer"],
            )
            show_message(self, "Receipt", "Receipt saved.", "success")
            os.startfile(path)
        except Exception as exc:
            show_message(self, "Receipt Error", str(exc), "error")

    def refresh(self) -> None:
        if self.selected_patient:
            self._refresh_history()
