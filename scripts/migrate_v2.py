"""
Database migration V2 — run once to add new columns/tables.
Safe to re-run: each step checks before altering.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from database.connection import SessionLocal


def col_exists(conn, table: str, column: str) -> bool:
    r = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=:t AND COLUMN_NAME=:c"
    ), {"t": table, "c": column}).scalar()
    return r > 0


def table_exists(conn, table: str) -> bool:
    r = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.TABLES "
        "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=:t"
    ), {"t": table}).scalar()
    return r > 0


def index_exists(conn, table: str, index: str) -> bool:
    r = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.STATISTICS "
        "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=:t AND INDEX_NAME=:i"
    ), {"t": table, "i": index}).scalar()
    return r > 0


def run(conn) -> None:
    steps = []

    # ── philhealth_records ─────────────────────────────────────────────────
    if not col_exists(conn, "philhealth_records", "case_type"):
        conn.execute(text(
            "ALTER TABLE philhealth_records "
            "ADD COLUMN case_type VARCHAR(20) DEFAULT 'Medical' AFTER case_description"
        ))
        steps.append("philhealth_records.case_type added")

    if not col_exists(conn, "philhealth_records", "health_facility_fee"):
        conn.execute(text(
            "ALTER TABLE philhealth_records "
            "ADD COLUMN health_facility_fee DECIMAL(12,2) DEFAULT 0.00 AFTER case_rate"
        ))
        steps.append("philhealth_records.health_facility_fee added")

    if not col_exists(conn, "philhealth_records", "professional_fee_amount"):
        conn.execute(text(
            "ALTER TABLE philhealth_records "
            "ADD COLUMN professional_fee_amount DECIMAL(12,2) DEFAULT 0.00 "
            "AFTER health_facility_fee"
        ))
        steps.append("philhealth_records.professional_fee_amount added")

    # Back-fill
    conn.execute(text(
        "UPDATE philhealth_records "
        "SET health_facility_fee = ROUND(case_rate * hospital_share_pct / 100, 2), "
        "    professional_fee_amount = ROUND(case_rate * professional_fee_pct / 100, 2) "
        "WHERE health_facility_fee = 0"
    ))
    steps.append("philhealth_records back-fill done")

    # ── billing_items ──────────────────────────────────────────────────────
    for col, ddl in [
        ("encoded_by", "INT DEFAULT NULL"),
        ("updated_by", "INT DEFAULT NULL"),
        ("encoded_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
        ("updated_at", "DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    ]:
        if not col_exists(conn, "billing_items", col):
            conn.execute(text(f"ALTER TABLE billing_items ADD COLUMN {col} {ddl}"))
            steps.append(f"billing_items.{col} added")

    # ── billings ───────────────────────────────────────────────────────────
    if not col_exists(conn, "billings", "soa_number"):
        conn.execute(text(
            "ALTER TABLE billings ADD COLUMN soa_number VARCHAR(30) DEFAULT NULL "
            "AFTER billing_number"
        ))
        steps.append("billings.soa_number added")

    if not col_exists(conn, "billings", "philhealth_case_rate_id"):
        conn.execute(text(
            "ALTER TABLE billings ADD COLUMN philhealth_case_rate_id INT DEFAULT NULL"
        ))
        conn.execute(text(
            "ALTER TABLE billings ADD CONSTRAINT fk_b_ph_case_rate "
            "FOREIGN KEY (philhealth_case_rate_id) REFERENCES philhealth_records(id)"
        ))
        steps.append("billings.philhealth_case_rate_id added")

    # ── charge_edit_log ────────────────────────────────────────────────────
    if not table_exists(conn, "charge_edit_log"):
        conn.execute(text("""
            CREATE TABLE charge_edit_log (
                id INT AUTO_INCREMENT PRIMARY KEY,
                billing_id INT NOT NULL,
                billing_item_id INT,
                action ENUM('ENCODE','EDIT','DELETE') NOT NULL,
                field_changed VARCHAR(100),
                old_value TEXT,
                new_value TEXT,
                performed_by INT NOT NULL,
                performed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (billing_id) REFERENCES billings(id),
                FOREIGN KEY (billing_item_id) REFERENCES billing_items(id),
                FOREIGN KEY (performed_by) REFERENCES users(id),
                INDEX idx_cel_billing (billing_id),
                INDEX idx_cel_user (performed_by),
                INDEX idx_cel_date (performed_at)
            ) ENGINE=InnoDB
        """))
        steps.append("charge_edit_log table created")

    # ── indexes ────────────────────────────────────────────────────────────
    if not index_exists(conn, "philhealth_records", "idx_ph_case_type"):
        conn.execute(text(
            "CREATE INDEX idx_ph_case_type ON philhealth_records(case_type)"
        ))
        steps.append("idx_ph_case_type index created")

    if not steps:
        print("  Nothing to migrate — database is already up to date.")
    else:
        for s in steps:
            print(f"  + {s}")


def main() -> None:
    print("=" * 55)
    print("Clinic CMS — Database Migration V2")
    print("=" * 55)
    session = SessionLocal()
    try:
        conn = session.connection()
        run(conn)
        # DDL in MySQL/MariaDB auto-commits; just close cleanly
        print("\nMigration completed successfully.")
    except Exception as exc:
        print(f"\nMigration FAILED: {exc}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
