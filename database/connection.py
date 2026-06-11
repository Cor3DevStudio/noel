"""Database engine and session management."""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from config.settings import DATABASE_URL
from utils.logger import logger

Base = declarative_base()
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@event.listens_for(engine, "connect")
def set_sql_mode(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("SET sql_mode='STRICT_TRANS_TABLES'")
    cursor.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as exc:
        session.rollback()
        logger.error("Database session error: %s", exc)
        raise
    finally:
        session.close()


def _migrate_schema() -> None:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("users")}
    if "permissions" not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN permissions JSON NULL"))
        logger.info("Added users.permissions column.")


def init_db() -> None:
    from models import (  # noqa: F401
        user, patient, appointment, consultation, prescription,
        medicine, billing, philhealth, settings_model, audit,
    )
    Base.metadata.create_all(bind=engine)
    _migrate_schema()
    logger.info("Database tables initialized.")
