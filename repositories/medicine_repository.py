from datetime import date, timedelta
from typing import List

from sqlalchemy.orm import Session, joinedload

from config.settings import EXPIRY_WARNING_DAYS, LOW_STOCK_THRESHOLD
from models.medicine import InventoryTransaction, Medicine, MedicineCategory, Supplier
from repositories.base_repository import BaseRepository


class MedicineRepository(BaseRepository[Medicine]):
    def __init__(self, session: Session) -> None:
        super().__init__(Medicine, session)

    def search(self, query: str, limit: int = 500) -> List[Medicine]:
        q = self.session.query(Medicine).filter(Medicine.is_active == True)
        if query:
            pattern = f"%{query}%"
            q = q.filter(
                Medicine.generic_name.ilike(pattern) | Medicine.brand_name.ilike(pattern)
            )
        return q.order_by(Medicine.generic_name).limit(limit).all()

    def get_low_stock(self) -> List[Medicine]:
        return (
            self.session.query(Medicine)
            .filter(Medicine.is_active == True, Medicine.stock_quantity <= Medicine.reorder_level)
            .all()
        )

    def get_expiring(self, days: int = EXPIRY_WARNING_DAYS) -> List[Medicine]:
        threshold = date.today() + timedelta(days=days)
        return (
            self.session.query(Medicine)
            .filter(
                Medicine.is_active == True,
                Medicine.expiration_date != None,
                Medicine.expiration_date <= threshold,
            )
            .order_by(Medicine.expiration_date)
            .all()
        )


class CategoryRepository(BaseRepository[MedicineCategory]):
    def __init__(self, session: Session) -> None:
        super().__init__(MedicineCategory, session)


class SupplierRepository(BaseRepository[Supplier]):
    def __init__(self, session: Session) -> None:
        super().__init__(Supplier, session)


class InventoryRepository(BaseRepository[InventoryTransaction]):
    def __init__(self, session: Session) -> None:
        super().__init__(InventoryTransaction, session)

    def get_by_medicine(self, medicine_id: int) -> List[InventoryTransaction]:
        return (
            self.session.query(InventoryTransaction)
            .filter(InventoryTransaction.medicine_id == medicine_id)
            .order_by(InventoryTransaction.created_at.desc())
            .all()
        )
