from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.connection import Base


class PhilHealthRecord(Base):
    __tablename__ = "philhealth_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    case_description: Mapped[str] = mapped_column(String(255), nullable=False)
    # 'Medical' = ICD-based (Annex A)  |  'Surgical' = RVS procedure-based (Annex B)
    case_type: Mapped[str] = mapped_column(String(20), default="Medical")
    case_rate: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    health_facility_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    professional_fee_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    price_effective_date: Mapped[Optional[date]] = mapped_column(Date)
    hospital_share_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=70)
    professional_fee_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=30)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    transactions: Mapped[list["PhilHealthTransaction"]] = relationship(
        "PhilHealthTransaction", back_populates="case_rate"
    )


class PhilHealthTransaction(Base):
    __tablename__ = "philhealth_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(Integer, ForeignKey("patients.id"), nullable=False)
    billing_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("billings.id"))
    consultation_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("consultations.id"))
    case_rate_id: Mapped[int] = mapped_column(Integer, ForeignKey("philhealth_records.id"), nullable=False)
    philhealth_number: Mapped[Optional[str]] = mapped_column(String(30))
    case_rate_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    hospital_share: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    professional_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    philhealth_deduction: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    patient_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    senior_discount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    pwd_discount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total_bill: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    processed_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    transaction_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    case_rate: Mapped["PhilHealthRecord"] = relationship("PhilHealthRecord", back_populates="transactions")
    patient: Mapped["Patient"] = relationship("Patient")


class PhilHealthClaimForm(Base):
    """Stores CF2, CF3, CF4, CF5 PhilHealth claim form submissions."""

    __tablename__ = "philhealth_claim_forms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    form_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    form_type: Mapped[str] = mapped_column(String(10), nullable=False)  # CF2, CF3, CF4, CF5
    status: Mapped[str] = mapped_column(String(30), default="Draft")   # Draft, Submitted, Approved, Rejected
    patient_id: Mapped[int] = mapped_column(Integer, ForeignKey("patients.id"), nullable=False)
    transaction_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("philhealth_transactions.id"))

    # Common fields
    philhealth_number: Mapped[Optional[str]] = mapped_column(String(30))
    date_of_claim: Mapped[Optional[date]] = mapped_column(Date)
    diagnosis: Mapped[Optional[str]] = mapped_column(String(500))
    icd_code: Mapped[Optional[str]] = mapped_column(String(50))
    case_rate_code: Mapped[Optional[str]] = mapped_column(String(50))
    total_amount_claimed: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    # CF2 / CF4 – Facility/Hospital fields
    admission_date: Mapped[Optional[date]] = mapped_column(Date)
    discharge_date: Mapped[Optional[date]] = mapped_column(Date)
    time_admitted: Mapped[Optional[str]] = mapped_column(String(10))       # HH:MM AM/PM
    time_discharged: Mapped[Optional[str]] = mapped_column(String(10))
    type_of_admission: Mapped[Optional[str]] = mapped_column(String(50))   # Ordinary, Emergency, Day Surgery
    patient_disposition: Mapped[Optional[str]] = mapped_column(String(60)) # Improved, Recovered, HAMA …
    accommodation_type: Mapped[Optional[str]] = mapped_column(String(30))  # Private / Non-Private
    admission_diagnosis: Mapped[Optional[str]] = mapped_column(Text)
    second_case_rate_code: Mapped[Optional[str]] = mapped_column(String(50))
    referring_hci: Mapped[Optional[str]] = mapped_column(String(200))
    attending_physician: Mapped[Optional[str]] = mapped_column(String(200))
    room_charges: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    medicine_charges: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    xray_lab_charges: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    other_charges: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    hospital_share: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    # CF3 – Professional Fee fields
    physician_name: Mapped[Optional[str]] = mapped_column(String(150))
    physician_prc_no: Mapped[Optional[str]] = mapped_column(String(50))
    physician_ptr_no: Mapped[Optional[str]] = mapped_column(String(50))
    physician_philhealth_no: Mapped[Optional[str]] = mapped_column(String(30))
    type_of_claim: Mapped[Optional[str]] = mapped_column(String(50))   # Primary, Specialist
    professional_fee_claimed: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    professional_fee_share: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    # CF5 – ESRD / Dialysis fields
    dialysis_center_name: Mapped[Optional[str]] = mapped_column(String(200))
    dialysis_center_accreditation: Mapped[Optional[str]] = mapped_column(String(50))
    period_from: Mapped[Optional[date]] = mapped_column(Date)
    period_to: Mapped[Optional[date]] = mapped_column(Date)
    number_of_sessions: Mapped[Optional[int]] = mapped_column(Integer)
    dialysis_type: Mapped[Optional[str]] = mapped_column(String(50))   # Hemodialysis, Peritoneal

    notes: Mapped[Optional[str]] = mapped_column(Text)
    prepared_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    # eClaims online transmission fields
    eclaim_ref_no: Mapped[Optional[str]] = mapped_column(String(50))
    eclaim_submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    eclaim_status: Mapped[str] = mapped_column(String(30), default="Pending")
    supporting_docs: Mapped[Optional[str]] = mapped_column(Text)   # JSON: [{path, doc_type}, ...]
    eclaim_notes: Mapped[Optional[str]] = mapped_column(Text)

    patient: Mapped["Patient"] = relationship("Patient")
    transaction: Mapped[Optional["PhilHealthTransaction"]] = relationship("PhilHealthTransaction")
