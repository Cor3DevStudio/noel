from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.connection import Base


class PhilHealthRecord(Base):
    __tablename__ = "philhealth_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    case_description: Mapped[str] = mapped_column(String(255), nullable=False)
    case_rate: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
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
