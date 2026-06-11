"""Authentication and user management service."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from config.settings import (
    PAGE_PERMISSIONS,
    ROLE_PERMISSIONS,
    SEED_ACCOUNTS,
)
from models.user import Role, User
from repositories.user_repository import RoleRepository, UserRepository
from services.activity_service import ActivityService
from utils.security import hash_password, session_manager, verify_password


class AuthService:
    def __init__(self, session: Session, activity_service: ActivityService | None = None) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.role_repo = RoleRepository(session)
        self.activity = activity_service or ActivityService(session)

    def initialize_roles(self) -> None:
        for role_name, permissions in ROLE_PERMISSIONS.items():
            existing = self.role_repo.get_by_name(role_name)
            if not existing:
                self.role_repo.create({
                    "name": role_name,
                    "description": f"{role_name} role",
                    "permissions": permissions,
                })
            else:
                # Keep DB permissions in sync with settings whenever the app starts
                self.role_repo.update(existing, {"permissions": permissions})

    def create_seed_accounts(self) -> None:
        """Create default demo accounts for each role if they do not exist yet."""
        for account in SEED_ACCOUNTS:
            if self.user_repo.get_by_username(account["username"]):
                continue
            role = self.role_repo.get_by_name(account["role"])
            if not role:
                continue
            self.user_repo.create({
                "role_id": role.id,
                "username": account["username"],
                "password_hash": hash_password(account["password"]),
                "full_name": account["full_name"],
                "email": account.get("email", ""),
                "is_active": True,
            })

    def create_default_admin(self) -> None:
        """Backward-compatible alias for startup seeding."""
        self.create_seed_accounts()

    def login(self, username: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        user = self.user_repo.get_by_username(username.strip())
        if not user:
            return False, "Invalid username or password.", None
        if not user.is_active:
            return False, "Account is deactivated. Contact administrator.", None
        if not verify_password(password, user.password_hash):
            return False, "Invalid username or password.", None

        user.last_login = datetime.now()
        self.session.flush()

        permissions = self.resolve_permissions(user)
        user_data = {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role.name,
            "role_id": user.role_id,
            "permissions": permissions,
        }
        session_manager.create_session(user_data)
        self._log_activity(user.id, "LOGIN", "Authentication", f"User {username} logged in.")
        return True, "Login successful.", user_data

    def logout(self) -> None:
        user = session_manager.get_current_user()
        if user:
            self._log_activity(user["id"], "LOGOUT", "Authentication", f"User {user['username']} logged out.")
        session_manager.clear_session()

    def change_password(self, user_id: int, current: str, new_password: str) -> Tuple[bool, str]:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False, "User not found."
        if not verify_password(current, user.password_hash):
            return False, "Current password is incorrect."
        if len(new_password) < 6:
            return False, "New password must be at least 6 characters."
        self.user_repo.update(user, {"password_hash": hash_password(new_password)})
        self._log_activity(user_id, "CHANGE_PASSWORD", "Authentication", "Password changed.")
        return True, "Password updated successfully."

    def change_username(self, user_id: int, new_username: str) -> Tuple[bool, str]:
        new_username = new_username.strip()
        if len(new_username) < 3:
            return False, "Username must be at least 3 characters."
        existing = self.user_repo.get_by_username(new_username)
        if existing and existing.id != user_id:
            return False, "Username already taken."
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False, "User not found."
        self.user_repo.update(user, {"username": new_username})
        current = session_manager.get_current_user()
        if current and current["id"] == user_id:
            current["username"] = new_username
            session_manager.set_current_user(current)
        return True, "Username updated successfully."

    def get_all_users(self) -> List[User]:
        return self.user_repo.get_active_users()

    def get_all_users_with_roles(self) -> List[User]:
        return self.user_repo.get_all_with_roles()

    @staticmethod
    def resolve_permissions(user: User) -> List[str]:
        if user.permissions is not None:
            return list(user.permissions)
        role_permissions = user.role.permissions if user.role else None
        if role_permissions:
            return list(role_permissions)
        return list(ROLE_PERMISSIONS.get(user.role.name if user.role else "", []))

    @staticmethod
    def role_default_permissions(user: User) -> List[str]:
        role_permissions = user.role.permissions if user.role else None
        if role_permissions:
            return list(role_permissions)
        return list(ROLE_PERMISSIONS.get(user.role.name if user.role else "", []))

    def get_user_permissions(self, user_id: int) -> Tuple[Optional[User], List[str], bool]:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return None, [], False
        uses_custom = user.permissions is not None
        return user, self.resolve_permissions(user), uses_custom

    def update_user_permissions(self, user_id: int, permissions: List[str]) -> Tuple[bool, str]:
        valid_keys = {key for key, _ in PAGE_PERMISSIONS}
        cleaned = [key for key in permissions if key in valid_keys]
        if not cleaned:
            return False, "Select at least one page for the user."

        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False, "User not found."

        role_defaults = self.role_default_permissions(user)
        if sorted(cleaned) == sorted(role_defaults):
            self.user_repo.update(user, {"permissions": None})
        else:
            self.user_repo.update(user, {"permissions": cleaned})

        current = session_manager.get_current_user()
        if current and current["id"] == user_id:
            current["permissions"] = cleaned
            session_manager.set_current_user(current)

        actor = session_manager.get_current_user()
        if actor:
            self._log_activity(
                actor["id"],
                "UPDATE_PERMISSIONS",
                "Users",
                f"Updated page access for {user.username}: {', '.join(cleaned)}",
            )
        return True, "User permissions saved. The user must sign out and back in for menu changes to apply."

    def reset_user_permissions(self, user_id: int) -> Tuple[bool, str]:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False, "User not found."
        self.user_repo.update(user, {"permissions": None})
        return True, "Permissions reset to role defaults."

    def create_user(self, data: dict) -> Tuple[bool, str, Optional[User]]:
        if self.user_repo.get_by_username(data["username"]):
            return False, "Username already exists.", None
        data["password_hash"] = hash_password(data.pop("password"))
        user = self.user_repo.create(data)
        current = session_manager.get_current_user()
        if current:
            self._log_activity(current["id"], "CREATE_USER", "Users", f"Created user {user.username}")
        return True, "User created successfully.", user

    def update_user(self, user_id: int, data: dict) -> Tuple[bool, str]:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False, "User not found."
        if "username" in data:
            new_username = str(data["username"]).strip()
            if len(new_username) < 3:
                return False, "Username must be at least 3 characters."
            existing = self.user_repo.get_by_username(new_username)
            if existing and existing.id != user_id:
                return False, "Username already taken."
            data["username"] = new_username
        if "password" in data and data["password"]:
            if len(data["password"]) < 6:
                return False, "Password must be at least 6 characters."
            data["password_hash"] = hash_password(data.pop("password"))
        else:
            data.pop("password", None)
        self.user_repo.update(user, data)
        current = session_manager.get_current_user()
        if current and current["id"] == user_id:
            if "username" in data:
                current["username"] = data["username"]
            if "full_name" in data:
                current["full_name"] = data["full_name"]
            if "role_id" in data and user.role:
                current["role"] = user.role.name
            session_manager.set_current_user(current)
        actor = session_manager.get_current_user()
        if actor:
            self._log_activity(actor["id"], "UPDATE_USER", "Users", f"Updated user {user.username}")
        return True, "User updated successfully."

    def reset_user_password(self, user_id: int, new_password: str) -> Tuple[bool, str]:
        if len(new_password) < 6:
            return False, "Password must be at least 6 characters."
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False, "User not found."
        self.user_repo.update(user, {"password_hash": hash_password(new_password)})
        actor = session_manager.get_current_user()
        if actor:
            self._log_activity(
                actor["id"], "RESET_PASSWORD", "Users", f"Reset password for {user.username}"
            )
        return True, f"Password reset for {user.username}."

    def toggle_user_status(self, user_id: int) -> Tuple[bool, str]:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False, "User not found."
        current = session_manager.get_current_user()
        if current and current["id"] == user_id:
            return False, "You cannot deactivate your own account."
        new_status = not user.is_active
        self.user_repo.update(user, {"is_active": new_status})
        status = "activated" if new_status else "deactivated"
        actor = session_manager.get_current_user()
        if actor:
            self._log_activity(
                actor["id"], "TOGGLE_USER", "Users", f"{status.capitalize()} user {user.username}"
            )
        return True, f"User {status} successfully."

    def get_roles(self) -> List[Role]:
        return self.role_repo.get_all()

    def get_doctors(self) -> List[User]:
        return self.user_repo.get_doctors()

    def _log_activity(self, user_id: int, action: str, module: str, description: str) -> None:
        self.activity.log(action, module, description, user_id=user_id)
