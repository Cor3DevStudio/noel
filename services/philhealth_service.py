"""PhilHealth benefit computation service."""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Optional, Tuple

from sqlalchemy.orm import Session

from config.settings import PWD_DISCOUNT_RATE, SENIOR_DISCOUNT_RATE
from models.patient import Patient
from models.philhealth import PhilHealthRecord, PhilHealthTransaction
from repositories.patient_repository import PatientRepository
from repositories.philhealth_repository import PhilHealthRepository, PhilHealthTransactionRepository
from utils.security import session_manager


class PhilHealthService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.rate_repo = PhilHealthRepository(session)
        self.transaction_repo = PhilHealthTransactionRepository(session)
        self.patient_repo = PatientRepository(session)

    def compute_benefits(
        self,
        patient_id: int,
        case_rate_id: int,
        total_bill: Decimal,
        apply_senior: bool = True,
        apply_pwd: bool = True,
    ) -> Dict[str, Decimal]:
        """Compute PhilHealth benefit breakdown."""
        patient = self.patient_repo.get_by_id(patient_id)
        case_rate = self.rate_repo.get_by_id(case_rate_id)
        if not patient or not case_rate:
            return {}

        total_bill = Decimal(str(total_bill))
        case_rate_amount = Decimal(str(case_rate.case_rate))
        hospital_pct = Decimal(str(case_rate.hospital_share_pct)) / Decimal("100")
        prof_pct = Decimal(str(case_rate.professional_fee_pct)) / Decimal("100")

        hospital_share = (case_rate_amount * hospital_pct).quantize(Decimal("0.01"), ROUND_HALF_UP)
        professional_fee = (case_rate_amount * prof_pct).quantize(Decimal("0.01"), ROUND_HALF_UP)
        philhealth_deduction = min(case_rate_amount, total_bill)

        remaining = total_bill - philhealth_deduction
        senior_discount = Decimal("0")
        pwd_discount = Decimal("0")

        if apply_senior and patient.is_senior_citizen:
            senior_discount = (remaining * Decimal(str(SENIOR_DISCOUNT_RATE))).quantize(
                Decimal("0.01"), ROUND_HALF_UP
            )
            remaining -= senior_discount
        elif apply_pwd and patient.is_pwd:
            pwd_discount = (remaining * Decimal(str(PWD_DISCOUNT_RATE))).quantize(
                Decimal("0.01"), ROUND_HALF_UP
            )
            remaining -= pwd_discount

        patient_balance = max(Decimal("0"), remaining).quantize(Decimal("0.01"), ROUND_HALF_UP)

        return {
            "case_rate_amount": case_rate_amount,
            "hospital_share": hospital_share,
            "professional_fee": professional_fee,
            "philhealth_deduction": philhealth_deduction,
            "senior_discount": senior_discount,
            "pwd_discount": pwd_discount,
            "patient_balance": patient_balance,
            "total_bill": total_bill,
        }

    def process_transaction(
        self,
        patient_id: int,
        case_rate_id: int,
        total_bill: Decimal,
        billing_id: int | None = None,
        consultation_id: int | None = None,
        notes: str = "",
    ) -> Tuple[bool, str, Optional[PhilHealthTransaction]]:
        patient = self.patient_repo.get_by_id(patient_id)
        if not patient:
            return False, "Patient not found.", None
        if not patient.philhealth_number:
            return False, "Patient has no PhilHealth number on file.", None

        computation = self.compute_benefits(patient_id, case_rate_id, total_bill)
        if not computation:
            return False, "Unable to compute PhilHealth benefits.", None

        user = session_manager.get_current_user()
        transaction = self.transaction_repo.create({
            "patient_id": patient_id,
            "billing_id": billing_id,
            "consultation_id": consultation_id,
            "case_rate_id": case_rate_id,
            "philhealth_number": patient.philhealth_number,
            "case_rate_amount": computation["case_rate_amount"],
            "hospital_share": computation["hospital_share"],
            "professional_fee": computation["professional_fee"],
            "philhealth_deduction": computation["philhealth_deduction"],
            "patient_balance": computation["patient_balance"],
            "senior_discount": computation["senior_discount"],
            "pwd_discount": computation["pwd_discount"],
            "total_bill": computation["total_bill"],
            "notes": notes,
            "processed_by": user["id"] if user else None,
        })
        return True, "PhilHealth transaction processed.", transaction

    def get_case_rates(self) -> list[PhilHealthRecord]:
        return self.rate_repo.get_active_rates()

    def create_case_rate(self, data: dict) -> Tuple[bool, str]:
        if self.rate_repo.get_by_code(data["case_code"]):
            return False, "Case code already exists."
        self.rate_repo.create(data)
        return True, "Case rate created successfully."

    def update_case_rate(self, rate_id: int, data: dict) -> Tuple[bool, str]:
        rate = self.rate_repo.get_by_id(rate_id)
        if not rate:
            return False, "Case rate not found."
        self.rate_repo.update(rate, data)
        return True, "Case rate updated successfully."

    def get_patient_history(self, patient_id: int) -> list[PhilHealthTransaction]:
        return self.transaction_repo.get_by_patient(patient_id)
