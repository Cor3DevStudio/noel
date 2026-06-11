"""Billing and payment service."""

from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from config.settings import PWD_DISCOUNT_RATE, SENIOR_DISCOUNT_RATE
from models.billing import Billing, BillingItem, Payment
from models.patient import Patient
from repositories.billing_repository import BillingRepository, PaymentRepository
from repositories.patient_repository import PatientRepository
from utils.security import generate_receipt_number, session_manager


class BillingService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.billing_repo = BillingRepository(session)
        self.payment_repo = PaymentRepository(session)
        self.patient_repo = PatientRepository(session)

    def create_billing(self, patient_id: int, items: List[dict], consultation_id: int | None = None) -> Tuple[bool, str, Optional[Billing]]:
        patient = self.patient_repo.get_by_id(patient_id)
        if not patient:
            return False, "Patient not found.", None

        subtotal = Decimal("0")
        billing_items = []
        for item in items:
            qty = int(item.get("quantity", 1))
            unit_price = Decimal(str(item.get("unit_price", 0)))
            total = qty * unit_price
            subtotal += total
            billing_items.append({
                "item_type": item.get("item_type", "Other"),
                "description": item["description"],
                "quantity": qty,
                "unit_price": unit_price,
                "total_price": total,
                "medicine_id": item.get("medicine_id"),
            })

        discount_amount, discount_type = self._calculate_discount(patient, subtotal)
        total = subtotal - discount_amount
        user = session_manager.get_current_user()

        billing = self.billing_repo.create({
            "billing_number": self.billing_repo.get_next_number(),
            "patient_id": patient_id,
            "consultation_id": consultation_id,
            "subtotal": subtotal,
            "discount_amount": discount_amount,
            "discount_type": discount_type,
            "total_amount": total,
            "balance": total,
            "payment_status": "Unpaid",
            "created_by": user["id"] if user else None,
        })

        for item_data in billing_items:
            item_data["billing_id"] = billing.id
            self.session.add(BillingItem(**item_data))

        self.session.flush()
        return True, "Billing created successfully.", billing

    def apply_philhealth_deduction(self, billing_id: int, deduction: Decimal) -> Tuple[bool, str]:
        billing = self.billing_repo.get_by_id(billing_id)
        if not billing:
            return False, "Billing not found."
        billing.philhealth_deduction = deduction
        billing.total_amount = max(Decimal("0"), billing.subtotal - billing.discount_amount - deduction)
        billing.balance = billing.total_amount - billing.amount_paid
        self._update_payment_status(billing)
        return True, "PhilHealth deduction applied."

    def record_payment(
        self, billing_id: int, amount: Decimal, method: str = "Cash", notes: str = ""
    ) -> Tuple[bool, str, Optional[Payment]]:
        billing = self.billing_repo.get_with_details(billing_id)
        if not billing:
            return False, "Billing not found.", None

        amount = Decimal(str(amount))
        if amount <= 0:
            return False, "Payment amount must be greater than zero.", None

        user = session_manager.get_current_user()
        payment = self.payment_repo.create({
            "billing_id": billing_id,
            "amount": amount,
            "payment_method": method,
            "receipt_number": generate_receipt_number(),
            "notes": notes,
            "received_by": user["id"] if user else None,
        })

        billing.amount_paid += amount
        billing.balance = max(Decimal("0"), billing.total_amount - billing.amount_paid)
        self._update_payment_status(billing)
        return True, "Payment recorded successfully.", payment

    def _calculate_discount(self, patient: Patient, subtotal: Decimal) -> Tuple[Decimal, str | None]:
        if patient.is_senior_citizen:
            return subtotal * Decimal(str(SENIOR_DISCOUNT_RATE)), "Senior Citizen (20%)"
        if patient.is_pwd:
            return subtotal * Decimal(str(PWD_DISCOUNT_RATE)), "PWD (20%)"
        return Decimal("0"), None

    def _update_payment_status(self, billing: Billing) -> None:
        if billing.balance <= 0:
            billing.payment_status = "Paid"
        elif billing.amount_paid > 0:
            billing.payment_status = "Partial"
        else:
            billing.payment_status = "Unpaid"

    def get_today_revenue(self) -> Decimal:
        return self.billing_repo.get_today_revenue()

    def get_monthly_revenue(self) -> Decimal:
        return self.billing_repo.get_monthly_revenue()

    def get_by_id(self, billing_id: int) -> Optional[Billing]:
        return self.billing_repo.get_with_details(billing_id)

    def get_by_patient(self, patient_id: int) -> List[Billing]:
        return self.billing_repo.get_by_patient(patient_id)
