"""Billing and payment service."""

from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from config.settings import ECLAIMS_DIR, PWD_DISCOUNT_RATE, SENIOR_DISCOUNT_RATE
from models.billing import Billing, BillingItem, Payment
from models.patient import Patient
from models.philhealth import PhilHealthRecord
from reports.soa_xml_generator import SoaXmlGenerator
from repositories.billing_repository import BillingRepository, PaymentRepository
from repositories.patient_repository import PatientRepository
from repositories.philhealth_repository import PhilHealthRepository
from utils.security import generate_receipt_number, session_manager


class BillingService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.billing_repo = BillingRepository(session)
        self.payment_repo = PaymentRepository(session)
        self.patient_repo = PatientRepository(session)
        self.rate_repo = PhilHealthRepository(session)

    def create_billing(self, patient_id: int, items: List[dict], consultation_id: int | None = None) -> Tuple[bool, str, Optional[Billing]]:
        patient = self.patient_repo.get_by_id(patient_id)
        if not patient:
            return False, "Patient not found.", None

        user = session_manager.get_current_user()
        subtotal = Decimal("0")
        billing_items = []
        for item in items:
            qty = int(item.get("quantity", 1))
            unit_price = Decimal(str(item.get("unit_price", 0)))
            total = qty * unit_price
            subtotal += total
            price_as_of = item.get("price_as_of")
            if price_as_of and not isinstance(price_as_of, date):
                price_as_of = date.today()
            billing_items.append({
                "item_type":   item.get("item_type", "Other"),
                "description": item["description"],
                "quantity":    qty,
                "unit_price":  unit_price,
                "total_price": total,
                "price_as_of": price_as_of or date.today(),
                "medicine_id": item.get("medicine_id"),
                "encoded_by":  user["id"] if user else None,
            })

        discount_amount, discount_type = self._calculate_discount(patient, subtotal)
        total = subtotal - discount_amount

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

    def get_weekly_revenue_data(self) -> list:
        return self.billing_repo.get_weekly_revenue_data()

    def get_by_id(self, billing_id: int) -> Optional[Billing]:
        return self.billing_repo.get_with_details(billing_id)

    def get_by_patient(self, patient_id: int) -> List[Billing]:
        return self.billing_repo.get_by_patient(patient_id)

    def get_by_date_range(self, start, end) -> list:
        return self.billing_repo.get_by_date_range(start, end)

    def get_income_summary(self, start, end) -> dict:
        return self.billing_repo.get_income_summary(start, end)

    def get_yearly_revenue(self, year: int) -> Decimal:
        return self.billing_repo.get_yearly_revenue(year)

    def get_monthly_revenue_by_year(self, year: int) -> list:
        return self.billing_repo.get_monthly_revenue_by_year(year)

    def _snapshot_philhealth_rate(self, billing: Billing, case_rate: PhilHealthRecord) -> None:
        """Lock PhilHealth amounts on the bill so future rate changes won't alter it."""
        billing.ph_snapshot_case_code = case_rate.case_code
        billing.ph_snapshot_case_description = case_rate.case_description
        billing.ph_snapshot_case_type = case_rate.case_type
        billing.ph_snapshot_case_rate = case_rate.case_rate
        billing.ph_snapshot_hff = case_rate.health_facility_fee
        billing.ph_snapshot_pf = case_rate.professional_fee_amount
        billing.ph_snapshot_effective_date = case_rate.price_effective_date or date.today()

    def _philhealth_display(self, billing: Billing) -> dict:
        """Return PhilHealth rate info — prefer snapshotted values from billing time."""
        if billing.ph_snapshot_case_code:
            live = billing.philhealth_case_rate if hasattr(billing, "philhealth_case_rate") else None
            return {
                "case_code": live.case_code if live else billing.ph_snapshot_case_code,
                "case_description": billing.ph_snapshot_case_description or "",
                "case_type": billing.ph_snapshot_case_type or "",
                "case_rate": float(billing.ph_snapshot_case_rate or 0),
                "health_facility_fee": float(billing.ph_snapshot_hff or 0),
                "professional_fee_ph": float(billing.ph_snapshot_pf or 0),
                "effective_date": billing.ph_snapshot_effective_date,
            }
        case_rate = billing.philhealth_case_rate if hasattr(billing, "philhealth_case_rate") else None
        if not case_rate:
            return {}
        return {
            "case_code": case_rate.case_code,
            "case_description": case_rate.case_description,
            "case_type": case_rate.case_type,
            "case_rate": float(case_rate.case_rate),
            "health_facility_fee": float(case_rate.health_facility_fee),
            "professional_fee_ph": float(case_rate.professional_fee_amount),
            "effective_date": case_rate.price_effective_date,
        }

    def get_soa_data(self, billing_id: int) -> Optional[dict]:
        """Gather all data needed to generate an SOA PDF."""
        billing = self.billing_repo.get_with_details(billing_id)
        if not billing:
            return None
        patient = billing.patient
        ph = self._philhealth_display(billing)
        items = [
            {
                "description": it.description,
                "item_type":   it.item_type,
                "quantity":    it.quantity,
                "unit_price":  float(it.unit_price),
                "total_price": float(it.total_price),
                "price_as_of": it.price_as_of,
                "encoded_by":  it.encoded_by,
            }
            for it in (billing.items or [])
        ]
        return {
            "billing":            billing,
            "patient":            patient,
            "items":              items,
            "philhealth":         ph,
            "case_rate":          billing.philhealth_case_rate,
            "soa_number":         billing.soa_number or self.billing_repo.get_next_soa_number(),
        }

    def assign_soa_number(self, billing_id: int) -> Tuple[bool, str]:
        billing = self.billing_repo.get_by_id(billing_id)
        if not billing:
            return False, "Billing not found."
        if not billing.soa_number:
            billing.soa_number = self.billing_repo.get_next_soa_number()
        return True, billing.soa_number

    def set_philhealth_case_rate(
        self, billing_id: int, case_rate_id: int, deduction: Decimal
    ) -> Tuple[bool, str]:
        billing = self.billing_repo.get_by_id(billing_id)
        if not billing:
            return False, "Billing not found."
        case_rate = self.rate_repo.get_by_id(case_rate_id)
        if not case_rate:
            return False, "Case rate not found."
        billing.philhealth_case_rate_id = case_rate_id
        self._snapshot_philhealth_rate(billing, case_rate)
        ok, msg = self.apply_philhealth_deduction(billing_id, deduction)
        return ok, msg

    def attach_soa_xml_to_eclaims(
        self,
        billing_id: int,
        philhealth_service,
        clinic_info: dict,
    ) -> Tuple[bool, str, Optional[str]]:
        """Generate SOA XML and attach it to the patient's eClaim supporting documents."""
        soa_data = self.get_soa_data(billing_id)
        if not soa_data:
            return False, "Could not load billing data.", None

        billing = soa_data["billing"]
        patient = soa_data["patient"]
        ph = soa_data.get("philhealth") or {}

        self.assign_soa_number(billing_id)
        billing = self.billing_repo.get_by_id(billing_id)
        soa_number = billing.soa_number or soa_data["soa_number"]

        out_dir = ECLAIMS_DIR / "soa"
        out_dir.mkdir(parents=True, exist_ok=True)
        xml_filename = f"SOA_{soa_number.replace('/', '-')}.xml"
        xml_path = str(out_dir / xml_filename)

        payload = {
            "soa_number": soa_number,
            "billing_number": billing.billing_number,
            "clinic_name": clinic_info.get("clinic_name", "Clinic"),
            "clinic_address": clinic_info.get("clinic_address", ""),
            "patient_name": patient.full_name,
            "philhealth_number": patient.philhealth_number or "",
            "admission_date": str(billing.created_at.date()),
            "discharge_date": str(billing.updated_at.date()),
            "items": soa_data["items"],
            "subtotal": float(billing.subtotal),
            "discount_amount": float(billing.discount_amount),
            "discount_type": billing.discount_type or "",
            "philhealth_deduction": float(billing.philhealth_deduction),
            "total_amount": float(billing.total_amount),
            "amount_paid": float(billing.amount_paid),
            "balance": float(billing.balance),
            "case_code": ph.get("case_code", ""),
            "case_description": ph.get("case_description", ""),
            "case_type": ph.get("case_type", ""),
            "case_rate": ph.get("case_rate", 0),
            "health_facility_fee": ph.get("health_facility_fee", 0),
            "professional_fee_ph": ph.get("professional_fee_ph", 0),
            "ph_effective_date": str(ph.get("effective_date") or ""),
        }

        try:
            SoaXmlGenerator.generate(xml_path, payload)
        except Exception as exc:
            return False, f"Failed to generate SOA XML: {exc}", None

        self.billing_repo.update(billing, {"soa_xml_path": xml_path})

        ok, msg, form_number = philhealth_service.attach_soa_xml_to_eclaim(
            patient.id, xml_path
        )
        if not ok:
            return False, msg, None

        return True, (
            f"SOA XML generated and attached to eClaim {form_number}.\n"
            f"File: {xml_path}\n"
            "It will appear automatically when you transmit the claim."
        ), xml_path
