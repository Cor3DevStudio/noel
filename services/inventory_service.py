"""Medicine inventory service."""

from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from models.medicine import InventoryTransaction, Medicine
from repositories.medicine_repository import (
    CategoryRepository, InventoryRepository, MedicineRepository, SupplierRepository,
)
from utils.security import session_manager


class InventoryService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.medicine_repo = MedicineRepository(session)
        self.category_repo = CategoryRepository(session)
        self.supplier_repo = SupplierRepository(session)
        self.inventory_repo = InventoryRepository(session)

    def add_medicine(self, data: dict) -> Tuple[bool, str, Optional[Medicine]]:
        medicine = self.medicine_repo.create(data)
        return True, "Medicine added successfully.", medicine

    def update_medicine(self, medicine_id: int, data: dict) -> Tuple[bool, str]:
        medicine = self.medicine_repo.get_by_id(medicine_id)
        if not medicine:
            return False, "Medicine not found."
        self.medicine_repo.update(medicine, data)
        return True, "Medicine updated successfully."

    def stock_in(self, medicine_id: int, quantity: int, **kwargs) -> Tuple[bool, str]:
        medicine = self.medicine_repo.get_by_id(medicine_id)
        if not medicine:
            return False, "Medicine not found."
        if quantity <= 0:
            return False, "Quantity must be positive."

        user = session_manager.get_current_user()
        self.inventory_repo.create({
            "medicine_id": medicine_id,
            "transaction_type": "Stock In",
            "quantity": quantity,
            "batch_number": kwargs.get("batch_number"),
            "expiration_date": kwargs.get("expiration_date"),
            "unit_cost": kwargs.get("unit_cost"),
            "reference_number": kwargs.get("reference_number"),
            "notes": kwargs.get("notes"),
            "performed_by": user["id"] if user else None,
        })
        medicine.stock_quantity += quantity
        if kwargs.get("batch_number"):
            medicine.batch_number = kwargs["batch_number"]
        if kwargs.get("expiration_date"):
            medicine.expiration_date = kwargs["expiration_date"]
        return True, f"Stock in: +{quantity} units."

    def stock_out(self, medicine_id: int, quantity: int, notes: str = "") -> Tuple[bool, str]:
        medicine = self.medicine_repo.get_by_id(medicine_id)
        if not medicine:
            return False, "Medicine not found."
        if quantity <= 0:
            return False, "Quantity must be positive."
        if medicine.stock_quantity < quantity:
            return False, f"Insufficient stock. Available: {medicine.stock_quantity}"

        user = session_manager.get_current_user()
        self.inventory_repo.create({
            "medicine_id": medicine_id,
            "transaction_type": "Stock Out",
            "quantity": quantity,
            "notes": notes,
            "performed_by": user["id"] if user else None,
        })
        medicine.stock_quantity -= quantity
        return True, f"Stock out: -{quantity} units."

    def adjust_stock(self, medicine_id: int, new_quantity: int, reason: str) -> Tuple[bool, str]:
        medicine = self.medicine_repo.get_by_id(medicine_id)
        if not medicine:
            return False, "Medicine not found."
        diff = new_quantity - medicine.stock_quantity
        user = session_manager.get_current_user()
        self.inventory_repo.create({
            "medicine_id": medicine_id,
            "transaction_type": "Adjustment",
            "quantity": abs(diff),
            "notes": f"Adjustment: {reason} (from {medicine.stock_quantity} to {new_quantity})",
            "performed_by": user["id"] if user else None,
        })
        medicine.stock_quantity = new_quantity
        return True, "Stock adjusted successfully."

    def search(self, query: str) -> List[Medicine]:
        return self.medicine_repo.search(query)

    def get_low_stock(self) -> List[Medicine]:
        return self.medicine_repo.get_low_stock()

    def get_expiring(self) -> List[Medicine]:
        return self.medicine_repo.get_expiring()

    def get_history(self, medicine_id: int) -> List[InventoryTransaction]:
        return self.inventory_repo.get_by_medicine(medicine_id)

    def get_categories(self):
        return self.category_repo.get_all()

    def get_suppliers(self):
        return self.supplier_repo.get_all()

    def add_category(self, name: str, description: str = "") -> Tuple[bool, str]:
        self.category_repo.create({"name": name, "description": description})
        return True, "Category added."

    def add_supplier(self, data: dict) -> Tuple[bool, str]:
        self.supplier_repo.create(data)
        return True, "Supplier added."
