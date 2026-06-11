"""
Import PhilHealth Case Rates from official PDF annexes into the database.

Usage:
    python scripts/import_philhealth_rates.py

PDFs are searched in:
    eclaims/
    assets/philhealth/
    %USERPROFILE%/Downloads/

Populates philhealth_records. Safe to re-run (upserts by case_code).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.connection import SessionLocal, ensure_database_exists
from database.seed_philhealth_rates import (
    ANNEX_CANDIDATES,
    load_pdf_records,
    upsert_rates,
    _resolve_annex_path,
)


def main() -> int:
    print("=" * 62)
    print("PhilHealth Case Rates Import")
    print("=" * 62)

    ensure_database_exists()

    found_any = False
    for filename, label, _case_type in ANNEX_CANDIDATES:
        path = _resolve_annex_path(filename)
        if path:
            found_any = True
            print(f"  Found: {path}")
        else:
            print(f"  Missing: {filename}")

    if not found_any:
        print("\n[ERROR] No PhilHealth annex PDFs found.")
        print("Place the official PDFs in the eclaims/ folder, then re-run.")
        return 1

    print("\nReading PDFs and importing rates...")
    records = load_pdf_records()
    if not records:
        print("[ERROR] No case rates could be parsed from the PDFs.")
        return 1

    session = SessionLocal()
    try:
        inserted, updated = upsert_rates(session, records)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    print(f"\n[COMPLETE] {inserted} inserted, {updated} updated ({len(records)} unique codes).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
