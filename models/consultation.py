from datetime import date, datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.connection import Base

if TYPE_CHECKING:
    from models.patient import Patient
    from models.user import User


class Consultation(Base):
    __tablename__ = "consultations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    appointment_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("appointments.id"))
    consultation_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    chief_complaint: Mapped[Optional[str]] = mapped_column(Text)
    vital_signs: Mapped[Optional[dict]] = mapped_column(JSON)
    diagnosis: Mapped[Optional[str]] = mapped_column(Text)
    treatment_plan: Mapped[Optional[str]] = mapped_column(Text)
    doctor_notes: Mapped[Optional[str]] = mapped_column(Text)
    follow_up_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="In Progress")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="consultations")
    doctor: Mapped["User"] = relationship("User", foreign_keys=[doctor_id])
    prescriptions: Mapped[list["Prescription"]] = relationship("Prescription", back_populates="consultation")
