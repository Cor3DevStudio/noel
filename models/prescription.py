from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.connection import Base

if TYPE_CHECKING:
    from models.consultation import Consultation


class Prescription(Base):
    __tablename__ = "prescriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    consultation_id: Mapped[int] = mapped_column(Integer, ForeignKey("consultations.id"), nullable=False)
    patient_id: Mapped[int] = mapped_column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    prescription_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    doctor_signature: Mapped[Optional[str]] = mapped_column(String(255))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    consultation: Mapped["Consultation"] = relationship("Consultation", back_populates="prescriptions")
    items: Mapped[list["PrescriptionItem"]] = relationship(
        "PrescriptionItem", back_populates="prescription", cascade="all, delete-orphan"
    )


class PrescriptionItem(Base):
    __tablename__ = "prescription_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prescription_id: Mapped[int] = mapped_column(Integer, ForeignKey("prescriptions.id"), nullable=False)
    medicine_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("medicines.id"))
    medicine_name: Mapped[str] = mapped_column(String(200), nullable=False)
    dosage: Mapped[Optional[str]] = mapped_column(String(100))
    frequency: Mapped[Optional[str]] = mapped_column(String(100))
    duration: Mapped[Optional[str]] = mapped_column(String(100))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    instructions: Mapped[Optional[str]] = mapped_column(Text)

    prescription: Mapped["Prescription"] = relationship("Prescription", back_populates="items")
