"""Input validation utilities."""

import re
from datetime import date, datetime
from typing import Optional


def validate_required(value: str, field_name: str) -> Optional[str]:
    if not value or not str(value).strip():
        return f"{field_name} is required."
    return None


def validate_email(email: str) -> Optional[str]:
    if not email:
        return None
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email.strip()):
        return "Invalid email format."
    return None


def validate_phone(phone: str) -> Optional[str]:
    if not phone:
        return None
    cleaned = re.sub(r"[\s\-()]", "", phone)
    if not re.match(r"^(\+63|0)?9\d{9}$", cleaned) and not re.match(r"^\d{7,15}$", cleaned):
        return "Invalid phone number format."
    return None


def validate_philhealth_number(number: str) -> Optional[str]:
    if not number:
        return None
    cleaned = re.sub(r"[\s\-]", "", number)
    if len(cleaned) < 10:
        return "PhilHealth number must be at least 10 characters."
    return None


def validate_positive_number(value: str, field_name: str) -> Optional[str]:
    try:
        num = float(value)
        if num < 0:
            return f"{field_name} must be a positive number."
    except (ValueError, TypeError):
        return f"{field_name} must be a valid number."
    return None


def parse_date(value: str) -> Optional[date]:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def sanitize_string(value: str, max_length: int = 255) -> str:
    if not value:
        return ""
    return str(value).strip()[:max_length]
