"""Security utilities for password hashing and session management."""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import bcrypt


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


class SessionManager:
    """In-memory session management for desktop application."""

    def __init__(self) -> None:
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._current_user: Optional[Dict[str, Any]] = None

    def create_session(self, user_data: Dict[str, Any]) -> str:
        token = secrets.token_hex(32)
        self._sessions[token] = {
            "user": user_data,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(hours=8),
        }
        self._current_user = user_data
        return token

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        return self._current_user

    def set_current_user(self, user_data: Dict[str, Any]) -> None:
        self._current_user = user_data

    def clear_session(self) -> None:
        self._current_user = None

    def is_authenticated(self) -> bool:
        return self._current_user is not None

    def has_permission(self, module: str) -> bool:
        if not self._current_user:
            return False
        permissions = self._current_user.get("permissions", [])
        return module in permissions


session_manager = SessionManager()


def generate_receipt_number(prefix: str = "OR") -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    suffix = hashlib.md5(secrets.token_bytes(4)).hexdigest()[:4].upper()
    return f"{prefix}-{timestamp}-{suffix}"
