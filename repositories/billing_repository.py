from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from models.billing import Billing, BillingItem, Payment
from repositories.base_repository import BaseRepository
from utils.security import session_manager


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

    def get_weekly_revenue_data(self) -> list:
        """Returns last 7 days revenue as list of (day_label, float) oldest-first."""
        from datetime import timedelta
        today = date.today()
        result = []
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            rev = (
                self.session.query(func.coalesce(func.sum(Payment.amount), 0))
                .filter(func.date(Payment.payment_date) == d)
                .scalar()
            )
            result.append((d.strftime("%a"), float(rev or 0)))
        return result

    def get_by_date_range(self, start: date, end: date) -> list:
        return (
            self.session.query(Billing)
            .options(joinedload(Billing.patient))
            .filter(func.date(Billing.created_at) >= start,
                    func.date(Billing.created_at) <= end)
            .order_by(Billing.created_at.desc())
            .all()
        )

    def get_yearly_revenue(self, year: int) -> Decimal:
        result = (
            self.session.query(func.coalesce(func.sum(Payment.amount), 0))
            .filter(func.year(Payment.payment_date) == year)
            .scalar()
        )
        return Decimal(str(result or 0))

    def get_monthly_revenue_by_year(self, year: int) -> list:
        """Returns 12 months' collected amounts for a given year [(month_label, float)]."""
        import calendar
        result = []
        for month in range(1, 13):
            rev = (
                self.session.query(func.coalesce(func.sum(Payment.amount), 0))
                .filter(
                    func.year(Payment.payment_date) == year,
                    func.month(Payment.payment_date) == month,
                )
                .scalar()
            )
            result.append((calendar.month_abbr[month], float(rev or 0)))
        return result

    def get_income_summary(self, start: date, end: date) -> dict:
        billings = self.get_by_date_range(start, end)
        total_billed    = sum(float(b.total_amount) for b in billings)
        total_collected = sum(float(b.amount_paid)  for b in billings)
        total_balance   = sum(float(b.balance)       for b in billings)
        return {
            "total_billed":    total_billed,
            "total_collected": total_collected,
            "total_balance":   total_balance,
            "count":           len(billings),
        }

    def get_next_number(self) -> str:
        from utils.helpers import generate_billing_number
        return generate_billing_number(self.count() + 1)

    def get_next_soa_number(self) -> str:
        today = datetime.now()
        prefix = f"SOA-{today.strftime('%Y%m%d')}"
        count = (
            self.session.query(func.count(Billing.id))
            .filter(Billing.soa_number.like(f"{prefix}%"))
            .scalar()
        ) or 0
        return f"{prefix}-{count + 1:04d}"


class PaymentRepository(BaseRepository[Payment]):
    def __init__(self, session: Session) -> None:
        super().__init__(Payment, session)
