from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.connection import Base

if TYPE_CHECKING:
    from models.patient import Patient


class Billing(Base):
    __tablename__ = "billings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    billing_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    patient_id: Mapped[int] = mapped_column(Integer, ForeignKey("patients.id"), nullable=False)
    consultation_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("consultations.id"))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    discount_type: Mapped[Optional[str]] = mapped_column(String(30))
    philhealth_deduction: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    payment_status: Mapped[str] = mapped_column(String(20), default="Unpaid")
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="billings")
    items: Mapped[list["BillingItem"]] = relationship(
        "BillingItem", back_populates="billing", cascade="all, delete-orphan"
    )
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="billing")


class BillingItem(Base):
    __tablename__ = "billing_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    billing_id: Mapped[int] = mapped_column(Integer, ForeignKey("billings.id"), nullable=False)
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    medicine_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("medicines.id"))

    billing: Mapped["Billing"] = relationship("Billing", back_populates="items")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    billing_id: Mapped[int] = mapped_column(Integer, ForeignKey("billings.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(20), default="Cash")
    receipt_number: Mapped[Optional[str]] = mapped_column(String(50))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    received_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    payment_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    billing: Mapped["Billing"] = relationship("Billing", back_populates="payments")
