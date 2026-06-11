"""General helper utilities."""

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Union


def format_currency(amount: Union[float, Decimal, int, None]) -> str:
    if amount is None:
        return "₱0.00"
    value = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"₱{value:,.2f}"


def format_date(value: Optional[Union[date, datetime]]) -> str:
    if not value:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%B %d, %Y")
    return value.strftime("%B %d, %Y")


def format_price_as_of(value: Optional[Union[date, datetime]]) -> str:
    """Short date label for price-effective displays (e.g. 'Jun 11, 2026')."""
    if not value:
        return "—"
    d = value.date() if isinstance(value, datetime) else value
    return d.strftime("%b %d, %Y")


def format_datetime(value: Optional[datetime]) -> str:
    if not value:
        return ""
    return value.strftime("%B %d, %Y %I:%M %p")


def calculate_age(birth_date: Optional[date]) -> Optional[int]:
    if not birth_date:
        return None
    today = date.today()
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age


def generate_patient_number(sequence: int) -> str:
    year = datetime.now().year
    return f"PAT-{year}-{sequence:05d}"


def generate_billing_number(sequence: int) -> str:
    year = datetime.now().year
    return f"BIL-{year}-{sequence:05d}"


def truncate_text(text: str, max_length: int = 50) -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."
