"""Database engine and session management."""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from config.settings import DATABASE_URL, SCHEMA_VERSION, SCHEMA_VERSION_FILE
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
    tables = set(inspector.get_table_names())

    if "users" not in tables:
        return

    # users.permissions
    users_cols = {c["name"] for c in inspector.get_columns("users")}
    if "permissions" not in users_cols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN permissions JSON NULL"))
        logger.info("Added users.permissions column.")

    # eClaims columns on philhealth_claim_forms
    if "philhealth_claim_forms" in tables:
        cf_cols = {c["name"] for c in inspector.get_columns("philhealth_claim_forms")}
        eclaim_cols = [
            ("eclaim_ref_no",       "VARCHAR(50) NULL"),
            ("eclaim_submitted_at", "DATETIME NULL"),
            ("eclaim_status",       "VARCHAR(30) NOT NULL DEFAULT 'Pending'"),
            ("supporting_docs",     "TEXT NULL"),
            ("eclaim_notes",        "TEXT NULL"),
        ]
        # re-read cols after potential earlier additions
        cf_cols = {c["name"] for c in inspector.get_columns("philhealth_claim_forms")}
        new_cf_cols = eclaim_cols + [
            ("time_admitted",        "VARCHAR(10) NULL"),
            ("time_discharged",      "VARCHAR(10) NULL"),
            ("patient_disposition",  "VARCHAR(60) NULL"),
            ("accommodation_type",   "VARCHAR(30) NULL"),
            ("admission_diagnosis",  "TEXT NULL"),
            ("second_case_rate_code","VARCHAR(50) NULL"),
            ("referring_hci",        "VARCHAR(200) NULL"),
            ("attending_physician",  "VARCHAR(200) NULL"),
        ]
        for col_name, col_def in new_cf_cols:
            if col_name not in cf_cols:
                with engine.begin() as conn:
                    conn.execute(text(
                        f"ALTER TABLE philhealth_claim_forms ADD COLUMN {col_name} {col_def}"
                    ))
                logger.info("Added philhealth_claim_forms.%s column.", col_name)

    if "billings" in tables:
        bill_cols = {c["name"] for c in inspector.get_columns("billings")}
        billing_new_cols = [
            ("soa_number", "VARCHAR(30) NULL"),
            ("soa_xml_path", "VARCHAR(500) NULL"),
            ("philhealth_case_rate_id", "INT NULL"),
        ]
        for col_name, col_def in billing_new_cols:
            if col_name not in bill_cols:
                with engine.begin() as conn:
                    conn.execute(text(
                        f"ALTER TABLE billings ADD COLUMN {col_name} {col_def}"
                    ))
                logger.info("Added billings.%s column.", col_name)
        ph_snapshot_cols = [
            ("ph_snapshot_case_code",        "VARCHAR(20) NULL"),
            ("ph_snapshot_case_description", "VARCHAR(255) NULL"),
            ("ph_snapshot_case_type",        "VARCHAR(20) NULL"),
            ("ph_snapshot_case_rate",        "DECIMAL(12,2) NULL"),
            ("ph_snapshot_hff",              "DECIMAL(12,2) NULL"),
            ("ph_snapshot_pf",               "DECIMAL(12,2) NULL"),
            ("ph_snapshot_effective_date",   "DATE NULL"),
        ]
        bill_cols = {c["name"] for c in inspector.get_columns("billings")}
        for col_name, col_def in ph_snapshot_cols:
            if col_name not in bill_cols:
                with engine.begin() as conn:
                    conn.execute(text(
                        f"ALTER TABLE billings ADD COLUMN {col_name} {col_def}"
                    ))
                logger.info("Added billings.%s column.", col_name)

    if "billing_items" in tables:
        bi_cols = {c["name"] for c in inspector.get_columns("billing_items")}
        billing_item_cols = [
            ("price_as_of", "DATE NULL"),
            ("encoded_by", "INT NULL"),
            ("updated_by", "INT NULL"),
            ("encoded_at", "DATETIME NULL"),
            ("updated_at", "DATETIME NULL"),
        ]
        for col_name, col_def in billing_item_cols:
            if col_name not in bi_cols:
                with engine.begin() as conn:
                    conn.execute(text(
                        f"ALTER TABLE billing_items ADD COLUMN {col_name} {col_def}"
                    ))
                logger.info("Added billing_items.%s column.", col_name)

    if "medicines" in tables:
        med_cols = {c["name"] for c in inspector.get_columns("medicines")}
        if "price_effective_date" not in med_cols:
            with engine.begin() as conn:
                conn.execute(text(
                    "ALTER TABLE medicines ADD COLUMN price_effective_date DATE NULL"
                ))
            logger.info("Added medicines.price_effective_date column.")

    if "philhealth_records" in tables:
        ph_cols = {c["name"] for c in inspector.get_columns("philhealth_records")}
        ph_new_cols = [
            ("price_effective_date", "DATE NULL"),
            ("case_type", "VARCHAR(20) NOT NULL DEFAULT 'Medical'"),
            ("health_facility_fee", "DECIMAL(12, 2) NOT NULL DEFAULT 0.00"),
            ("professional_fee_amount", "DECIMAL(12, 2) NOT NULL DEFAULT 0.00"),
        ]
        for col_name, col_def in ph_new_cols:
            if col_name not in ph_cols:
                with engine.begin() as conn:
                    conn.execute(text(
                        f"ALTER TABLE philhealth_records ADD COLUMN {col_name} {col_def}"
                    ))
                logger.info("Added philhealth_records.%s column.", col_name)

    if "clinic_settings" in tables:
        cs_cols = {c["name"] for c in inspector.get_columns("clinic_settings")}
        if "consultation_fee_effective_date" not in cs_cols:
            with engine.begin() as conn:
                conn.execute(text(
                    "ALTER TABLE clinic_settings ADD COLUMN consultation_fee_effective_date DATE NULL"
                ))
            logger.info("Added clinic_settings.consultation_fee_effective_date column.")


def _read_schema_version() -> int:
    try:
        if SCHEMA_VERSION_FILE.exists():
            return int(SCHEMA_VERSION_FILE.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        pass
    return 0


def _write_schema_version(version: int) -> None:
    SCHEMA_VERSION_FILE.write_text(str(version), encoding="utf-8")


def _migrate_schema_if_needed() -> None:
    if _read_schema_version() >= SCHEMA_VERSION:
        return
    _migrate_schema()
    _write_schema_version(SCHEMA_VERSION)


def ensure_database_exists() -> None:
    """Create the MySQL database if it does not exist yet."""
    import pymysql

    from config.settings import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER

    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD or None,
        charset="utf8mb4",
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.commit()
        logger.info("Database '%s' is ready.", DB_NAME)
    finally:
        conn.close()


def ensure_db_connection() -> None:
    """Lightweight connectivity check — no schema migration."""
    ensure_database_exists()
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))


def init_db(run_migrations: bool = True) -> None:
    from models import (  # noqa: F401
        user, patient, appointment, consultation, prescription,
        medicine, billing, philhealth, settings_model, audit,
    )
    Base.metadata.create_all(bind=engine)
    if run_migrations:
        _migrate_schema_if_needed()
    logger.info("Database tables initialized.")
