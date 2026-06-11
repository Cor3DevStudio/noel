from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.connection import Base


class MedicineCategory(Base):
    __tablename__ = "medicine_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    medicines: Mapped[list["Medicine"]] = relationship("Medicine", back_populates="category")


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    contact_person: Mapped[Optional[str]] = mapped_column(String(150))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(150))
    address: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    medicines: Mapped[list["Medicine"]] = relationship("Medicine", back_populates="supplier")


class Medicine(Base):
    __tablename__ = "medicines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("medicine_categories.id"))
    supplier_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("suppliers.id"))
    generic_name: Mapped[str] = mapped_column(String(200), nullable=False)
    brand_name: Mapped[Optional[str]] = mapped_column(String(200))
    dosage_form: Mapped[Optional[str]] = mapped_column(String(100))
    strength: Mapped[Optional[str]] = mapped_column(String(100))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    selling_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    price_effective_date: Mapped[Optional[date]] = mapped_column(Date)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    reorder_level: Mapped[int] = mapped_column(Integer, default=10)
    batch_number: Mapped[Optional[str]] = mapped_column(String(50))
    expiration_date: Mapped[Optional[date]] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    category: Mapped[Optional["MedicineCategory"]] = relationship("MedicineCategory", back_populates="medicines")
    supplier: Mapped[Optional["Supplier"]] = relationship("Supplier", back_populates="medicines")

    @property
    def display_name(self) -> str:
        if self.brand_name:
            return f"{self.generic_name} ({self.brand_name})"
        return self.generic_name


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    medicine_id: Mapped[int] = mapped_column(Integer, ForeignKey("medicines.id"), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    batch_number: Mapped[Optional[str]] = mapped_column(String(50))
    expiration_date: Mapped[Optional[date]] = mapped_column(Date)
    unit_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    reference_number: Mapped[Optional[str]] = mapped_column(String(50))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    performed_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    medicine: Mapped["Medicine"] = relationship("Medicine")
