from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from models.billing import Billing, BillingItem, Payment
from repositories.base_repository import BaseRepository


class BillingRepository(BaseRepository[Billing]):
    def __init__(self, session: Session) -> None:
        super().__init__(Billing, session)

    def get_with_details(self, billing_id: int) -> Optional[Billing]:
        return (
            self.session.query(Billing)
            .options(
                joinedload(Billing.patient),
                joinedload(Billing.items),
                joinedload(Billing.payments),
            )
            .filter(Billing.id == billing_id)
            .first()
        )

    def get_by_patient(self, patient_id: int) -> List[Billing]:
        return (
            self.session.query(Billing)
            .filter(Billing.patient_id == patient_id)
            .order_by(Billing.created_at.desc())
            .all()
        )

    def get_today_revenue(self) -> Decimal:
        today = date.today()
        result = (
            self.session.query(func.coalesce(func.sum(Payment.amount), 0))
            .filter(func.date(Payment.payment_date) == today)
            .scalar()
        )
        return Decimal(str(result or 0))

    def get_monthly_revenue(self) -> Decimal:
        today = date.today()
        start = today.replace(day=1)
        result = (
            self.session.query(func.coalesce(func.sum(Payment.amount), 0))
            .filter(
                func.date(Payment.payment_date) >= start,
                func.date(Payment.payment_date) <= today,
            )
            .scalar()
        )
        return Decimal(str(result or 0))

    def get_next_number(self) -> str:
        from utils.helpers import generate_billing_number
        return generate_billing_number(self.count() + 1)


class PaymentRepository(BaseRepository[Payment]):
    def __init__(self, session: Session) -> None:
        super().__init__(Payment, session)
