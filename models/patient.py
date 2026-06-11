from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.connection import Base


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    suffix: Mapped[Optional[str]] = mapped_column(String(20))
    birth_date: Mapped[Optional[date]] = mapped_column(Date)
    gender: Mapped[str] = mapped_column(String(10), default="Other")
    civil_status: Mapped[Optional[str]] = mapped_column(String(30))
    contact_number: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(150))
    address_street: Mapped[Optional[str]] = mapped_column(String(255))
    address_barangay: Mapped[Optional[str]] = mapped_column(String(100))
    address_city: Mapped[Optional[str]] = mapped_column(String(100))
    address_province: Mapped[Optional[str]] = mapped_column(String(100))
    address_zip: Mapped[Optional[str]] = mapped_column(String(10))
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(150))
    emergency_contact_relationship: Mapped[Optional[str]] = mapped_column(String(50))
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(String(20))
    philhealth_number: Mapped[Optional[str]] = mapped_column(String(30))
    philhealth_category: Mapped[Optional[str]] = mapped_column(String(50))
    philhealth_member_type: Mapped[Optional[str]] = mapped_column(String(50))
    is_senior_citizen: Mapped[bool] = mapped_column(Boolean, default=False)
    senior_id_number: Mapped[Optional[str]] = mapped_column(String(50))
    is_pwd: Mapped[bool] = mapped_column(Boolean, default=False)
    pwd_id_number: Mapped[Optional[str]] = mapped_column(String(50))
    photo_path: Mapped[Optional[str]] = mapped_column(String(500))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    appointments: Mapped[list["Appointment"]] = relationship("Appointment", back_populates="patient")
    consultations: Mapped[list["Consultation"]] = relationship("Consultation", back_populates="patient")
    billings: Mapped[list["Billing"]] = relationship("Billing", back_populates="patient")

    @property
    def full_name(self) -> str:
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.last_name)
        if self.suffix:
            parts.append(self.suffix)
        return " ".join(parts)

    @property
    def full_address(self) -> str:
        parts = [
            self.address_street, self.address_barangay,
            self.address_city, self.address_province, self.address_zip,
        ]
        return ", ".join(p for p in parts if p)
