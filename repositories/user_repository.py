from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from models.user import Role, User
from repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: Session) -> None:
        super().__init__(User, session)

    def get_by_id(self, record_id: int) -> Optional[User]:
        return (
            self.session.query(User)
            .options(joinedload(User.role))
            .filter(User.id == record_id)
            .first()
        )

    def get_by_username(self, username: str) -> Optional[User]:
        return (
            self.session.query(User)
            .options(joinedload(User.role))
            .filter(User.username == username)
            .first()
        )

    def get_active_users(self) -> List[User]:
        return (
            self.session.query(User)
            .options(joinedload(User.role))
            .filter(User.is_active == True)
            .all()
        )

    def get_all_with_roles(self) -> List[User]:
        return (
            self.session.query(User)
            .options(joinedload(User.role))
            .order_by(User.full_name)
            .all()
        )

    def get_doctors(self) -> List[User]:
        return (
            self.session.query(User)
            .join(Role)
            .filter(Role.name == "Doctor", User.is_active == True)
            .all()
        )


class RoleRepository(BaseRepository[Role]):
    def __init__(self, session: Session) -> None:
        super().__init__(Role, session)

    def get_by_name(self, name: str) -> Optional[Role]:
        return self.session.query(Role).filter(Role.name == name).first()
