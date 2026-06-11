"""Base repository with common CRUD operations."""

from typing import Generic, List, Optional, Type, TypeVar

from sqlalchemy.orm import Session

from database.connection import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: Session) -> None:
        self.model = model
        self.session = session

    def get_by_id(self, record_id: int) -> Optional[ModelType]:
        return self.session.get(self.model, record_id)

    def get_all(self, limit: int = 1000) -> List[ModelType]:
        return self.session.query(self.model).limit(limit).all()

    def create(self, data: dict) -> ModelType:
        instance = self.model(**data)
        self.session.add(instance)
        self.session.flush()
        return instance

    def update(self, instance: ModelType, data: dict) -> ModelType:
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        self.session.flush()
        return instance

    def delete(self, instance: ModelType) -> None:
        self.session.delete(instance)
        self.session.flush()

    def count(self) -> int:
        return self.session.query(self.model).count()
