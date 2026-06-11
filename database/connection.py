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
        if "soa_xml_path" not in bill_cols:
            with engine.begin() as conn:
                conn.execute(text(
                    "ALTER TABLE billings ADD COLUMN soa_xml_path VARCHAR(500) NULL"
                ))
            logger.info("Added billings.soa_xml_path column.")
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
        if "price_as_of" not in bi_cols:
            with engine.begin() as conn:
                conn.execute(text(
                    "ALTER TABLE billing_items ADD COLUMN price_as_of DATE NULL"
                ))
            logger.info("Added billing_items.price_as_of column.")

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
        if "price_effective_date" not in ph_cols:
            with engine.begin() as conn:
                conn.execute(text(
                    "ALTER TABLE philhealth_records ADD COLUMN price_effective_date DATE NULL"
                ))
            logger.info("Added philhealth_records.price_effective_date column.")

    if "clinic_settings" in tables:
        cs_cols = {c["name"] for c in inspector.get_columns("clinic_settings")}
        if "consultation_fee_effective_date" not in cs_cols:
            with engine.begin() as conn:
                conn.execute(text(
                    "ALTER TABLE clinic_settings ADD COLUMN consultation_fee_effective_date DATE NULL"
                ))
            logger.info("Added clinic_settings.consultation_fee_effective_date column.")


def init_db() -> None:
    from models import (  # noqa: F401
        user, patient, appointment, consultation, prescription,
        medicine, billing, philhealth, settings_model, audit,
    )
    Base.metadata.create_all(bind=engine)
    _migrate_schema()
    logger.info("Database tables initialized.")
