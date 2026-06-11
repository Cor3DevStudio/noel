from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.connection import Base


class ClinicSettings(Base):
    __tablename__ = "clinic_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    clinic_name: Mapped[str] = mapped_column(String(200), default="Clinic Management System")
    clinic_address: Mapped[Optional[str]] = mapped_column(Text)
    clinic_phone: Mapped[Optional[str]] = mapped_column(String(50))
    clinic_email: Mapped[Optional[str]] = mapped_column(String(150))
    clinic_logo_path: Mapped[Optional[str]] = mapped_column(String(500))
    receipt_header: Mapped[Optional[str]] = mapped_column(Text)
    receipt_footer: Mapped[Optional[str]] = mapped_column(Text)
    consultation_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=500)
    consultation_fee_effective_date: Mapped[Optional[date]] = mapped_column(Date)
    tax_id: Mapped[Optional[str]] = mapped_column(String(50))
    philhealth_accreditation: Mapped[Optional[str]] = mapped_column(String(50))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
